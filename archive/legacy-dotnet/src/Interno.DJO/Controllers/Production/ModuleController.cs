using System;
using System.Data;
using System.Collections.Generic;
using System.Linq;

using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

using System.ComponentModel.DataAnnotations;
using System.Text.Json.Serialization;
using Interno.DJO.Helpers;

namespace Interno.DJO.Controllers
{
    [ApiController]
    [Route("[Controller]")]
    public class ModuleController : ControllerBase
    {
        private readonly DJOContext _context;
        private readonly Interno.Production.Models.ProductionContext _production;
        public ModuleController(Interno.DJO.DJOContext context, Interno.Production.Models.ProductionContext production)
        {
            _context = context;
            _production = production;
            var temp = _context.Results.Where(r => r.Date.Hour == 0).Include(s => s.Shift);
            //Arreglamos los Result que no tengan Hora de Inicio en el Registro y Agregamos la hora de inicio del Turno
            foreach (var result in temp)
            {
                if(result.Date.TimeOfDay ==  TimeSpan.Zero){
                    result.Date = result.Date.Date.AddTicks(result.Shift.DateStart.TimeOfDay.Ticks);
                    _context.Results.Update(result);
                }
            }
            _context.SaveChanges();
        }

        [HttpGetAttribute]
        public IActionResult getModules()
        {
            //Creamos regitros de los modulos segun el BOM
            var mod = _context.BOMs.Where(b => b.Module != "").GroupBy(b => b.Module).Select(b => b.Key).ToList();
            foreach (var item in mod)
            {
                if(!_context.Resources.Any(r => r.Code == item)){
                    Production.Models.Resource res = new Production.Models.Resource();
                    res.Code = item;
                    res.Name = item;
                    res.TypeId = 4;
                    _context.Resources.Add(res);
                }
            }
            _context.SaveChanges();
            return Ok(_context.Resources.ToList());
        }

        //Informacion del Modulo en base al Codigo
        [HttpGet("{code}")]
        public IActionResult getModuleResult(string code)
        {
            code = code.ToUpper();//Codigo de Modulo a Mayusculas
            var shift = this.getShift();//Cargamos el Turno Actual
            
            //Cargamos Informacion del Result
            Interno.Production.Models.Result result = this.getModuleNowResult(code);//Cargamos Resultados del Modulo
            
            if(result.Resource == null){ //Si no tiene modulo el Result se los Asignamos
                result.Resource = _production.Resource.FirstOrDefault(r => r.Code == code);
                if(result.Resource.Code != null) { result.ResourceCode = result.Resource.Code;}
            }
            if(result.Shift == null){ //Si el result no tienen el Shift se lo Asignamos
                result.Shift = shift;
                if(result.Shift != null){ result.ShiftId = result.Shift.Id;}
            } 
            //Agregamos Hora por Hora al Result
            result.HourByHour = _context.HourByHour.Where(h => h.ResultId == result.Id && h.Hour >= shift.DateStart).ToList();

            //Fecha y Hora Actual
            var now = DateTime.Now.Date;
            
            // var orders = _context.WorkOrders.Where(w => woIds.Contains(w.FinishItemCode) && w.Request.Date >= Interno.DJO.Helpers.InternoExtensions.FirstDayOfWeek(now).AddDays(-2).Date && w.Status == Domain.Enum.StatusType.Released ).ToList();
            // List<string> litems = orders.GroupBy(g => g.FinishItemCode).Select(s => s.Key).ToList();
            // return Ok(_context.BOMs.Where(b => litems.Contains(b.Item) && b.ComponentModule == code));

            //Cargamos las ordenes que esten dentro del Plan (primer dia de la semana Domingo - 2 Dias para cargar la fecha del Viernes pasado)
            List<Interno.Production.Models.WorkOrder> orders = _context.WorkOrders.Where(w => (w.Request.Date >= Interno.DJO.Helpers.InternoExtensions.FirstDayOfWeek(now).AddDays(-2).Date 
                        && w.Request.Date <= Interno.DJO.Helpers.InternoExtensions.LastDayOfWeek(now).Date) && w.OrderQty > w.ManufQty && w.Status == Domain.Enum.StatusType.Released)
                    .Join(_context.BOMs, Wo => Wo.FinishItemCode,bom => bom.Component, (wo,bom) => new{
                        Item = wo.FinishItemCode,
                        Module = bom.ComponentModule,
                        Type = bom.ComponentType,
                        WO = wo
                    }).Where(b => b.Module == code ).ToList().GroupBy(g => g.WO).Select(s => s.Key).OrderBy(o => o.Request.Date).ToList();
            // //&& b.Type == "MFG Finished Good"
            
            // if(result.Date == null){result.Date = DateTime.Now.Date; }
            
            List<string> items = orders.GroupBy(o => o.FinishItemCode).Select(s => s.Key).ToList();//Listado de Items
            List<Interno.Production.Models.OperationTime> times = _production.OperationTime.Where(t => items.Contains(t.Product) ).ToList();//StandartTimes de los Items
            //Recorremos las Ordenes
            foreach (var item in orders)
            {
                item.OperationTime = times.FirstOrDefault(t => t.Product == item.FinishItemCode);//Asignamos StandartTimes
                if(item.OperationTime != null){
                    item.EstimatedTime = item.OperationTime.RunTime * item.OrderQty;//Asignamos Tiempo Estimado
                }
            }

            //Cracion de Grafica
            Interno.Production.Models.ResourceGraphic graphic = new Production.Models.ResourceGraphic();
            //Mientras definimos como poners los grupos de descanzos para generar las Graficas de Descanzo
            result.Breaks = _context.BreaksGroups.FirstOrDefault(b => b.ShiftId == result.ShiftId);
            
            var initialHour = shift.Start.Hours;//Horario Inicial 6
            var date = DateTime.Now.Date.AddHours(initialHour);//Fecha con Horario Inicial del turno
            //Agregamos Horas desde Inicio del Turno
            for (int i = 0; i < Math.Ceiling( shift.AvailableTime.TotalHours); i++) graphic.hours.Add( date.AddHours(i).TimeOfDay);

            
            if(result.Breaks!=null)
            {//Cargamos los Brakes del Modulo
                List<int> brakesIds = _context.ShifGroupBrakes.Where(b => b.ShiftId == result.ShiftId && b.BreakGroupId == result.Breaks.Id).Select(b => b.BreakId).ToList();
                result.Breaks.Breaks = _context.Break.Where(b=> brakesIds.Contains(b.Id)).ToList();
                graphic.Breaks = result.Breaks.Breaks;
            }
            //Listado de Horarios para Grafica
            foreach (var item in graphic.hours)
            {
                graphic.Disponible.Add(1);//Hora completa disponible
                graphic.Meta.Add(0);
                graphic.Producidas.Add(0);
                graphic.Faltante.Add(0);
                graphic.Excedente.Add(0);
                graphic.Acumulate.Add(0);
                graphic.RealAcumulate.Add(0);
                graphic.Real.Add(0);
                graphic.Eficiencia.Add(0);
            }

            //Recorremos las Horas del Turno y Calculamos el Tiempo disponible
            if(graphic.Breaks != null){
                foreach (var item in graphic.Breaks)
                {
                    for (int i = 0; i < graphic.hours.Count; i++)
                    {
                        if(graphic.hours[i].TotalHours == item.Start.Hours){
                            //revisar Horas Quebradas
                            graphic.Disponible[i] = Math.Round( graphic.Disponible[i] + item.Duration.TotalHours ,2);
                        }
                    }
                }
            }
            
            
            //Agregamos Termino e Inicio del Turno al Listado de Tiempo Disponible
            if(shift.End.Minutes != 0){ graphic.Disponible[graphic.Disponible.Count-1] = (shift.End - graphic.hours[graphic.hours.Count-1]).TotalHours; }
            
            if(shift.Start.Minutes != 0){ graphic.Disponible[0] = (graphic.hours[1] - shift.Start).TotalHours; }
            //Agregamos el Tiempo Disponible
            foreach (var item in graphic.Disponible) graphic.Horas.Add(TimeSpan.FromHours(item)); 
            //Tiempo del Turno
            
            var totalBreaks = TimeSpan.FromHours(graphic.Breaks.Sum(b => b.Duration.TotalHours));//Calculamos total de tiempo en Descanzos
            var tiempoDisponible = graphic.Disponible.Sum(); //Cantidas en Horas Disponibles
            TimeSpan tDisponible = TimeSpan.Zero;
            foreach (var item in graphic.Horas) tDisponible = tDisponible + item;//Sumamos cada una de las horas para calcular el tiempo disponible
            tDisponible = tDisponible + totalBreaks;//Le restamos los Descanzos

            //Metas
            List<Interno.Production.Models.Goal> meta = this.getGoals(code);
            result.Goals = meta;
            foreach (var item in meta)
            {
                for (int i = 0; i < graphic.hours.Count; i++)
                {
                    if(item.Hour.Hours == graphic.hours[i].Hours) { graphic.Meta[i] = item.Qty; }
                }    
            }
            //cargamos Informacion del Hora por Hora 
            var hxh = result.HourByHour.OrderBy(h => h.Hour).GroupBy(h => h.Hour).Select(h => new {Hour = h.Key,  Meta = h.Sum(r => r.Meta),Producidas = h.Sum(r => r.Pieces) }).ToList();
            
            foreach (var item in hxh)
            {//Buscamos el horario de la Grafica
                
                var temp =  TimeSpan.FromHours(item.Hour.Hour);
                
                var index = graphic.hours.IndexOf(TimeSpan.FromHours(item.Hour.Hour));
                //Si existe el horario en la Grafica hacemos calculo para las graficas.
                if(index != -1){
                    graphic.Real[index] = item.Producidas;
                    if(graphic.Real[index] > graphic.Meta[index] && graphic.Meta[index] > 0){
                        graphic.Excedente[index] = graphic.Real[index] - Int16.Parse( graphic.Meta[index].ToString());
                        graphic.Faltante[index] = 0;
                        graphic.Producidas[index] = Int16.Parse( graphic.Meta[index].ToString());
                        graphic.Real[index] = graphic.Real[index] - graphic.Excedente[index];
                        
                    }else{
                        graphic.Faltante[index] = (graphic.Meta[index] > 0)? Int16.Parse( graphic.Meta[index].ToString()) - graphic.Real[index] : 0; 
                        graphic.Producidas[index] = graphic.Real[index];
                    }
                }
            }
            
            //Falta Crear Horarios Vacios cuando no tienen escaneo
        
            //Sum Downtime.
            List<Production.Models.Downtime> downtime =  _context.Downtimes.Where(d => d.Result.ResourceCode == result.ResourceCode 
                                                                && (d.Status != Domain.Enum.StatusType.Closed || d.Created.Date == DateTime.Now.Date)).ToList();

            //Labor Personal on Shift
            result.Labor = result.Labor.Where(l => l.Start >= shift.DateStart).ToList();

            //Numero de Empleados que registraron Labor
            var emp  = result.Labor.Where(l => l.TypeId == 0 && l.End == DateTime.MinValue).GroupBy(l => l.EmployeeNumber).Count();
            
            foreach (var item in graphic.hours)
            {//No recuerdo exactamente para que se usa, pero es para alguna grafica
                graphic.Categories.Add(item.ToString().Substring(0,2)+"-");
                //categories: ["06-", "07-", "08-", "09-", "10-", "11-", "12-", "13-", "14-", "15-", "16-", "17-"]
            }

           IEficiencia efi = new IEficiencia();
            //Calculo de Eficiencia por Hora
           for (int i = 0; i < graphic.Meta.Count-1; i++)
           {
                if(i > 0){
                    graphic.Acumulate[i] = Int32.Parse( Math.Round( graphic.Meta[i]).ToString()) + graphic.Acumulate[i-1];
                    if(shift.DateStart.Date.AddTicks(graphic.hours[i].Ticks) < DateTime.Now.AddHours(-1) ){
                        graphic.RealAcumulate[i] = graphic.Producidas[i]+ graphic.Excedente[i] + graphic.RealAcumulate[i-1];
                        if(graphic.RealAcumulate[i]!=0 && graphic.Acumulate[i]!=0){
                            graphic.Eficiencia[i] = (graphic.RealAcumulate[i]*100) / graphic.Acumulate[i];
                            efi = new IEficiencia{
                                Acumulado = graphic.Acumulate[i], 
                                RealAcumulado = graphic.RealAcumulate[i], 
                                Eficiencia = ((graphic.RealAcumulate[i]+graphic.Excedente[i])*100)/ graphic.Acumulate[i]};
                        }
                    }
                }else{
                    graphic.Acumulate[i] = Int32.Parse( Math.Round(graphic.Meta[i]).ToString());
                    graphic.RealAcumulate[i] = graphic.Producidas[i] + graphic.Excedente[i];
                }
           }
           //Cargar registros de Labor de Produccion
            var tLabor = result.Labor.Where(l => l.TypeId == 0).Sum(p => p.Transcurred.TotalHours);

            
            return Ok(new{
                WorkOrders = orders.OrderBy(o => o.Request),//Listado de Ordenes Activas en el Plan
                result,//Regitros de Produccion en el Modulo
                graphic,//Graficas del Modulo
                labor = new{ //Calculos de Labor para el Modulo
                    Employee =  emp,//Numero de Empleados Activos
                    Available = (DateTime.Now.Date.AddHours(shift.End.TotalHours) - DateTime.Now).TotalHours * emp,//Tiempo Disponible segun el Turno * Numero de Empleados
                    Disponible = graphic.Disponible.Sum() * emp,//10.99
                    Downtime = downtime.Sum(d => d.Transcurred.TotalHours),
                    Labor = tLabor,
                },
                eficiencia = efi,//Eficiencia del Modulo General
                hrEficienci = this.getEfficiency(result),//Eficiencia del Modulo por Hora
                machines = _context.Machines.Where(m => m.Module.Contains(code)) //Maquinas Asignadas al Modulo
            });
        }

        //Listados de Eficiencia por Hora del Modulo
        public List<Interno.DJO.Models.EfficiencyHrs> getEfficiency(Interno.Production.Models.Result result)
        {//Cargamos la Eficienca del Modulo Por Hora del Turno
            var hrEficienci = _context.EfficiencyHrs.Include(r => r.Result).Where(e => e.Result.ResourceCode == result.ResourceCode && e.Date >= result.Shift.DateStart && e.Date <= result.Shift.DateEnd).OrderBy(r => r.Date).ToList();
            var tempPain = 0;
            foreach (var item in hrEficienci)
            {//Numero de Empleados en el Turno Actual
                item.EmployeesQty = result.Labor.Where(l => l.Start.TimeOfDay.Hours <= item.Date.TimeOfDay.Hours && l.TypeId == 0 && (l.End == DateTime.MinValue || l.End.Hour == item.Hour)).Count();
                tempPain += item.EmployeesQty;
                item.PaidHrs = tempPain;//Horas pagadas segun numero de Empleados
            }
            return hrEficienci;
        }

        [HttpGet("ResultInit")]
        public IActionResult setInitResult()
        {
            var temp = _context.Results.Where(r => r.Date >= DateTime.Now.Date).Include(s => s.Shift);
            foreach (var result in temp)
            {
                if(result.Date.TimeOfDay ==  TimeSpan.Zero){
                    result.Date = result.Date.Date.AddTicks(result.Shift.DateStart.TimeOfDay.Ticks);
                    _context.Results.Update(result);
                }
            }
            return Ok(_context.SaveChanges());
        }

        //Informacion para el Supervisor del Modulo (Fecha y Modulo)
        [HttpPost("Admin")]
        public IActionResult getModuleAdmin(IModuleSupervisor data)
        {
            
            var temp = _context.Results
                .Include(r => r.Shift)
                .Include(r => r.Downtime)
                .Include(r => r.HourByHour)
                .Where(r => r.Created.Date == data.Date.Date && r.ResourceCode.ToUpper() == data.Module.ToUpper()).OrderBy(r => r.Id).ToList();
            //Tipos de Issue para el Calculo de Labor y Downtime
            List<Production.Models.ProdIssue> types = _context.Issues.ToList();
            foreach (var item in temp)
            {
                item.Labor = _context.Labors.Where(l => l.ResultId == item.Id).ToList();
                item.Goals = _context.Goals.Where(g => g.ResourceCode == item.ResourceCode ).ToList();
                var init = item.Date;
                var end = init.AddHours(item.Shift.Hours+1);
                //Mientras sea dentro del Turno Actual
                while (init < end && init < DateTime.Now)
                {
                    if(!item.HourByHour.Any(h => h.Hour.Date == init.Date && h.Hour.Hour == init.Hour))//Si no contiene registro de la Hora
                    {//Agregamos los datos de la hora, vacios para que no existan huecos en el turno ala hora del calculo de eficiencia
                        item.HourByHour.Add(new Production.Models.HourByHour{Hour = init,Meta = item.Goals.FirstOrDefault(g => g.Hour.Hours == init.TimeOfDay.Hours).Qty, ResultId = item.Id ,ResourceCode = item.ResourceCode});
                    }
                    init = init.AddHours(1);
                }
                item.HourByHour.OrderBy(h => h.Hour);
                _context.Results.Update(item);
            }
            _context.SaveChanges();
            return Ok(temp);
        }

        [HttpGet("Result/{code}")]
        public IActionResult getResult(string code)
        {
            var result = this.getModuleNowResult(code);
           return Ok(result);
        }

        [HttpPost("Result")]
        public IActionResult setResult(IResultSet data)
        {   
            //Separamos Item y Cantidad Escaneados ejem:  01E120'50 -> 01E120 = Numero de Parte, '50 = Cantidad de Piezas escaneadas
            var scan = data.Scan.Split("'", StringSplitOptions.RemoveEmptyEntries);//[0:Item,1:Qty]

            //validamos que no sean negativo el numero de Piezas y sea un numero valido
            if( scan.Length > 1 && Int32.Parse(scan[1]) <= 0){
                ModelState.AddModelError("Qty","The Qty entered is not allowed.");
            }
            //Validar si tiene WorkOrder el Item
            // var _wo = _context.WorkOrders.Where(w => w.FinishItemCode == scan[0] && w.OrderQty > (w.ManufQty + w.Count)).OrderBy(w => w.Request.Date).FirstOrDefault();

            // if( _wo != null){//Operacion Cancelada ya que puede correr el mismo numero de parte en diferentes modulos y no siempre es el asigndo
            //     //Validar Modulo del Item
            //     // var _bom = _context.BOMs.FirstOrDefault(b => b.ComponentModule == data.Module && b.Component == scan[0]);
            //     // if(_bom == null){ ModelState.AddModelError("Scan","The Part Number you cannot work in the Module."); }
            // }else{ ModelState.AddModelError("Scan","The Part Number has no pending WorkOrders or Not Exist."); }
            
            //Informacion sobre turno actual
            var shift = getShift();

            //Verifi Personal Labor
            // if(!_context.Labors.Any(l => l.ResourceCode == data.Module && l.Start.Date >= shift.DateStart))
            // {
            //     ModelState.AddModelError("Labor","It is necessary to register LABOR of the Personnel.");
            // }

            /// FALTA VALIDAR EL EMPLEADO ACTIVO Hasta no cargar el listado de Empleados desde el sistema Tress ///

            if(ModelState.IsValid)
            {
                var h = DateTime.Now.Date.AddHours(DateTime.Now.TimeOfDay.Hours).TimeOfDay;//Hora Actual sin Minutos
                //Result del Modulo en el Turno
                Interno.Production.Models.Result result = this.getModuleNowResult(data.Module);//Datos del Produccion del Modulo Actual
                //Cargamos Hora por Hora
                //result.HourByHour = _context.HourByHour.Where(r => r.ResultId ==  result.Id && r.Hour >= shift.DateStart).ToList();
                //Scan Qty
                //Si no se escaneo cantidad con el numero de Piezas
                var qty =(scan.Count()>1)? Int32.Parse(scan[1]) : 1;
                
                //Cargamos Hora Actual o Generamos registros
                Interno.Production.Models.HourByHour hour = result.HourByHour.FirstOrDefault(h => h.Hour.Hour == DateTime.Now.Hour) ?? new Production.Models.HourByHour();
                hour.Pieces+= qty;
                hour.ResourceCode = data.Module;
                
                if(hour.ResultId == 0){//Si es nuevo el registro de la hora actual
                    var meta = result.Goals.FirstOrDefault(g => g.ResourceCode ==  data.Module && g.Hour == h);//Cargamos la meta del Modulo ala hora actual
                    hour.Meta = (meta != null)? meta.Qty :0;
                    hour.ResourceCode = data.Module;
                    hour.ResultId = result.Id;
                    if(result.InitialTime == DateTime.MinValue){ result.InitialTime = DateTime.Now;}//Asignamos fecha de Inicio de Produccion
                    result.HourByHour.Add(hour);
                }
                var exist = _context.Results.FirstOrDefault(d => d.Id == result.Id);
                    if(exist != null){ _context.Entry(exist).State = EntityState.Detached; }
                _context.Results.Update(result);

                // //StdTime for Item
                Interno.Production.Models.OperationTime time = _production.OperationTime.FirstOrDefault(ot => ot.Product == scan[0]);
                if(time != null){
                    //Eficiencia del Modulo en la Hora Actual o nuevo registro de Eficiencia
                    Interno.DJO.Models.EfficiencyHrs efi = _context.EfficiencyHrs.FirstOrDefault(e => e.Date.Date == DateTime.Now.Date && e.Date.Hour == DateTime.Now.Hour && e.ResultId == result.Id && e.Item == scan[0]) 
                            ?? new Models.EfficiencyHrs{ 
                                ResourceCode = result.ResourceCode, 
                                ResultId = result.Id, 
                                Item = scan[0].ToUpper(),
                                StdTime = time.RunTime.TotalHours,
                                Meta = hour.Meta
                            };
                    efi.Pieces += qty;
                    //Contamos empleados registrados en el Modulo en la Hora Actual
                    efi.EmployeesQty = result.Labor.Where(l => l.Start.TimeOfDay.Hours <= shift.DateStart.TimeOfDay.Hours && l.TypeId == 0 && (l.End == DateTime.MinValue || l.End.Hour == DateTime.Now.Hour)).GroupBy(l=> l.EmployeeNumber).Count();
                    efi.PaidHrs = efi.EmployeesQty;
                    //Actualizamos datos de la Hora Actual (Eficiencia, Hora por Hora, Result)
                    _context.EfficiencyHrs.Update(efi);
                }
                //_wo = this.updateWorkOrderCount(_wo,qty);//Actualizacion de Informacion en la Work Order Cantidad Producida
                if(_context.SaveChanges()>0){
                    return Ok(result);
                } ModelState.AddModelError("Updated","Problems updating information.");
            }
            return BadRequest(ModelState);
        }

        //Metodo que actualiza la informacion de las Work Orders
        [HttpPost("WorkOrders")]
        [RequestFormLimits(MultipartBodyLengthLimit = 209715200)]
        [RequestSizeLimit(209715200)]
        public IActionResult setWorkOrders([FromForm] IFormFile file)
        {
            //Si contiene archivos 
            if(file.Length > 0){
                DataTable Report = ReportController.CSVtoDataTable( file.OpenReadStream());
                Object[] last = Report.Rows[Report.Rows.Count-1].ItemArray;

                List<string> _wo = Report.AsEnumerable().Select(w => w.Field<string>("job Name")).ToList();
                List<string> _items = Report.AsEnumerable().GroupBy(w => w.Field<string>("assY$Item")).Select(w =>w.Key).ToList();
                List<Interno.Production.Models.OperationTime> _operations = _production.OperationTime.Where(ot => _items.Contains( ot.Product )).ToList();
                List<Interno.Production.Models.WorkOrder> listWO = _context.WorkOrders.Where(w => _wo.Contains(w.Id)).ToList();
                
                int con = 0;
                var updated = 0;
                foreach (DataRow row in Report.Rows)
                {
                    Interno.Production.Models.WorkOrder wo = listWO.SingleOrDefault(w => w.Id == row["job Name"].ToString()) ?? new Production.Models.WorkOrder();
                    
                    wo.Id = row["job Name"].ToString();
                    wo.Type = (row["job Type"].ToString().Split(" ")[0] == "Standard")? Production.Models.WOType.Standard : Production.Models.WOType.NonStandard;
                    wo.FinishItemCode = row["assY$Item"].ToString();
                    
                    int qty;
                    Int32.TryParse(row["job Quantity Scheduled"].ToString(), out qty);
                    wo.OrderQty = qty;
                    
                    try{
                        wo.ManufQty = Convert.ToInt32(Math.Floor(Convert.ToDouble( row["job Quantity Completed"].ToString()))) ;
                    }catch(System.FormatException){ return BadRequest( row["job Quantity Completed"].ToString());}

                    switch (row["job Status"].ToString().Split(" ")[0])
                    {
                        case "Released": wo.Status = Domain.Enum.StatusType.Released; break;
                        case "Cancelled": wo.Status = Domain.Enum.StatusType.Canceled; break;
                        case "Closed": wo.Status = Domain.Enum.StatusType.Closed; break;
                        case "Complete": wo.Status = Domain.Enum.StatusType.Complete; break;
                        case "Complete - No Charges": wo.Status = Domain.Enum.StatusType.InPart; break;
                        case "Failed Close": wo.Status = Domain.Enum.StatusType.Damaged; break;
                        default: wo.Status = Domain.Enum.StatusType.StandBy; break;
                    }
                    
                    //wo.Status = (row["job Status"].ToString().Split(" ")[0] == "Released")? Domain.Enum.StatusType.Released : Domain.Enum.StatusType.StandBy;
                    wo.Release = DateTime.Parse(row["job Released Date"].ToString());
                    wo.Request = DateTime.Parse(row["job Scheduled Completion Dt"].ToString());
                    var OperationTime = _operations.Where(ot => ot.Product == wo.FinishItemCode).OrderByDescending(o => o.Created).FirstOrDefault();

                    if(OperationTime != null)
                    {
                        wo.OperationTimeId = OperationTime.Id;
                    }
                    wo.CustomerId = 1; //General
                    if(listWO.Any(w => w.Id == wo.Id)){
                        _production.WorkOrders.Update(wo);
                    }else{ _production.WorkOrders.Add(wo); }
                    
                    con++;
                    if((con % 1000) == 0){
                        updated += _context.SaveChanges();
                        Console.WriteLine(updated);
                    }
                }
                return Ok(updated);
            }
            return BadRequest();
        }
        
        //Metodo que registra Tiempo Muerto
        [HttpPost("Downtime")]
        public IActionResult setModuleDowntime(IDowntime downtime)
        {
            
            if(downtime.IssueId == 0) ModelState.AddModelError("Issue","Issue is reuqired");

            if(ModelState.IsValid){
                downtime.RequestNumber = downtime.Employee.getNumber();//Numero de Empleado que registro tiempo muerto
                Interno.Production.Models.Result result = this.getModuleNowResult(downtime.Module);//regsitro de Produccion del Modulo
                //Asiganamos registro de Produccion al tiempo Muerto                
                if(downtime.ResultId == 0) downtime.ResultId = result.Id;
                //Si el registro de tiempo muerto es actualizacion de Status Cerrado
                if(downtime.Status == Domain.Enum.StatusType.Closed ){ downtime.ClosedDate = DateTime.Now;}
                //Si no es un nuevo registro de Donwtime
                if(downtime.Id != 0){ 
                    var exist = _context.Downtimes.FirstOrDefault(d => d.Id == downtime.Id);
                    if(exist != null){ _context.Entry(exist).State = EntityState.Detached; }
                    
                    _context.Downtimes.Update(downtime);}
                else{ //agregamos registro de Downtime
                    downtime.Created = DateTime.Now;
                    _context.Downtimes.Add(downtime);
                 }
                try{
                    return Ok(_context.SaveChanges());
                }catch(Microsoft.EntityFrameworkCore.DbUpdateConcurrencyException){ModelState.AddModelError("Updated","Problems updating information.");}
            }
            return BadRequest(ModelState);
        }

        [HttpGet("Downtime/{code}")]//Registros de Downtime del Modulo en el Pendientes de Cierre y del Turno Actual
        public IActionResult getModuleDowntime(string code) => Ok( _context.Downtimes.Where(d => d.Result.ResourceCode == code && ( d.ClosedDate == DateTime.MinValue || d.ClosedDate.Date == DateTime.Now.Date)).ToList());

        //Metodo que asigna Labor al Modulo
        [HttpPost("Labor")]
        public IActionResult SetLaborResult(ILabor data) 
        { 
            if(ModelState.IsValid)
            {
                var shift = getShift();//Turno Actual
                //Registros de Labor del Empleado
                var registers = _context.Labors.Include(l => l.Result).OrderByDescending(l => l.Start).FirstOrDefault(l => l.EmployeeNumber == data.Employee.getNumber());
                
                if(registers != null){
                    //Si tiene registros de Labor de Turno Pasados Se actualizan al termino del Turno la fecha de Cierre
                    if(registers.Start <= shift.DateStart)
                    {   
                        if(registers.Start.TimeOfDay.TotalHours >= 18){
                            registers.End = registers.Start.Date.AddDays(1).AddHours(shift.End.TotalHours);
                        }else{
                            registers.End = registers.Start.Date.AddHours(shift.End.TotalHours);
                        }
                        
                    }else{//Si no tiene registro de Labor se crea uno nuevo
                        registers.End = DateTime.Now;
                        //Validamos si el empleado ya tiene un registro de labor en el turno actual
                        if(registers.TypeId == data.Type && registers.Start >= shift.DateStart)
                        {
                            ModelState.AddModelError("Labor","The employee already contains a record of the same type of Labor. Reference: "+ registers.Result.ResourceCode); 
                            return BadRequest(ModelState);
                        }
                    }
                    registers.ResourceCode = data.Module;
                    _context.Labors.Update(registers);
                    _context.SaveChanges();
                }
                
                //Create new Labor
                Production.Models.Labor labor = new Production.Models.Labor();
                labor.EmployeeNumber = data.Employee.getNumber();
                labor.Start = DateTime.Now;
                labor.TypeId = data.Type;
                
                //Cargamos datos del result del Modulo del Dia-Turno
                Interno.Production.Models.Result result = this.getModuleNowResult(data.Module);
                
                if(labor != null){
                    result.Labor.Add(labor);
                    
                    _context.Results.Update(result);
                }
                return Ok(_context.SaveChanges());
            }
            return BadRequest(ModelState);
        }

        //Metodo que actualiza las Metas del Modulo
        [HttpPost("Goals")]
        public IActionResult updateModuleGoals(List<Production.Models.Goal> data)
        {
            foreach (var item in data){ _context.AddOrUpdate(item); }
            return Ok(_context.SaveChanges());
        }
        
        //Actualizacion de ValueStream a los Modulos
        [HttpPost("ValueStream")]
        [RequestFormLimits(MultipartBodyLengthLimit = 209715200)]
        [RequestSizeLimit(209715200)]
        public IActionResult SetMachines([FromForm] IFormFile file)
        {
            //Si contiene archivos 
            if(file.Length > 0){
                DataTable Report = ReportController.ExcelToDataTable( file.OpenReadStream())[0];
                List<Production.Models.Resource> res = _context.Resources.ToList();
                for (int i = 2; i < Report.Rows.Count; i++)
                {
                    
                    var temp = res.FirstOrDefault(r => r.Code ==  Report.Rows[i][2].ToString());
                    if(temp != null){
                        temp.Description = Report.Rows[i][0].ToString();
                        _context.Resources.Update(temp);
                    } 
                    
                }
            }
            return Ok(_context.SaveChanges());
        }
        
        //Actualizacion de Labor
        [HttpPost("Result/Labor")]
        public IActionResult UpdateResultLabor(Production.Models.Labor data)
        {
            data.Start = data.Start.ToLocalTime();
            _context.Labors.Update(data);
            return Ok(_context.SaveChanges());
        }

        //Actualizacion de Piezas en el Hora por Hora del Supervisor
        [HttpPost("Result/Pieces")]
        public IActionResult UpdateResultPieces(Production.Models.HourByHour data)
        {
            //FALTA MODIFICAR LA EFICIENCIA
            _context.HourByHour.Update(data);
            if(_context.SaveChanges() > 0){

            }
            return Ok(_context.SaveChanges());
        }

        //Actualizacion del Downtime por el Supervisor
        [HttpPost("Result/Downtime")]
        public IActionResult UpdateResultDonwtime(Production.Models.Downtime data)
        {
            data.Created = data.Created.ToLocalTime();
            if(data.ClosedDate != DateTime.MinValue){ data.ClosedDate = data.ClosedDate.ToLocalTime(); }
            _context.Downtimes.Update(data);
            return Ok(_context.SaveChanges());
        }
        // [HttpPost("Supervisor")]
        // public IActionResult setSupervisors([FromForm] IFormFile file)
        // {
        //     //Si contiene archivos 
        //     if(file.Length > 0){
        //         UserController user = new UserController();
        //         DataTable Report = ReportController.ExcelToDataTable( file.OpenReadStream())[0];
        //         int updated = 0;
        //         try{
        //             for (int i = 0; i < Report.Rows.Count; i++)
        //             {
        //                 try{
        //                     var temp = user.findUser( Report.Rows[i].ItemArray[1].ToString());

        //                     //return Ok(temp);
        //                     if(temp != null){
        //                         var tuser = _context.Users.Include(u => u.Claims).FirstOrDefault(u => u.UserName == temp["samaccountname"].ToString()) ?? new DJO.Models.Users();
        //                         tuser.UserName = temp["samaccountname"][0].ToString();
        //                         try{
        //                             tuser.Email = temp["mail"][0].ToString();
        //                         }catch(System.ArgumentOutOfRangeException){}
        //                         tuser.DisplayName = temp["cn"][0].ToString();
        //                         var cla = new DJO.Models.InternoClaim();
        //                         cla.UserUserName = tuser.UserName;
        //                         cla.Claim = "supervisor";
        //                         cla.InternoRole = Models.InternoRoles.Supervisor;
        //                         tuser.Claims.Add(cla);
        //                         _context.Add(tuser);
        //                     }
        //                 }catch(System.NullReferenceException){
        //                     return BadRequest(Report.Rows[i].ItemArray[1].ToString());
        //                 }
        //                 updated += _context.SaveChanges();
        //             }
        //             return Ok(updated);
        //         }catch(Microsoft.EntityFrameworkCore.DbUpdateConcurrencyException){

        //         }
                
        //     }
        //     return BadRequest();
        // }
        
        private List<Production.Models.Goal> getGoals(string code)
        {
            code = code.ToUpper();
            List<Production.Models.Goal> goals = _context.Goals.Where(g => g.ResourceCode == code).ToList();
            var cero  = TimeSpan.Zero;
            for (int i = 0; i < 24; i++)
            {
                if(!goals.Any(g => g.Hour.Hours == i)){ goals.Add(new Production.Models.Goal{ResourceCode = code, Hour = TimeSpan.FromHours(i)}); }
            }
            return goals.OrderBy(g => g.Hour).ToList();
        }
        private Production.Models.WorkOrder updateWorkOrderCount(Production.Models.WorkOrder _wo, int qty)
        {
            if(_wo.MissingQty < qty)
            {
                var temp = _wo.MissingQty;
                _wo.Count+= _wo.MissingQty;
                _context.WorkOrders.Update(_wo);
                if(_context.SaveChanges() > 0){
                    qty = qty - temp;
                    Production.Models.WorkOrder _wo2 = _context.WorkOrders.Where(w => w.FinishItemCode == _wo.FinishItemCode && w.Request.Date <= DateTime.Now.Date && w.OrderQty > (w.ManufQty + w.Count)).OrderBy(w => w.Request.Date).FirstOrDefault();
                    _wo2.Count+=qty;
                    _context.WorkOrders.Update(_wo2);
                    if(_context.SaveChanges()>0)
                    {
                        return _wo2;
                    }
                }
            }else{
                _wo.Count+=qty;
                _context.WorkOrders.Update(_wo);
                if(_context.SaveChanges() > 0){
                    return _wo;
                }
            }
            return null;
        }

        //Metodo para solicitar datos de produccion por Modulo en el turno Actual
        public Production.Models.Result getModuleNowResult(string module)
        {
            var shift = this.getShift();//Turno Actual

            //Cargamos datos del Resultado del Modulo Actual /Turno/Registros de Downtime/ Hora por Hora/ Empleados registrados
            Production.Models.Result result = _context.Results
                .Include(r => r.Shift)
                .Include(r => r.Downtime)
                .Include(r => r.HourByHour)
                .Include(r => r.Labor)
                .FirstOrDefault(r => r.ResourceCode.ToUpper() == module.ToUpper() && r.Date >= shift.DateStart.AddMinutes(-1)) 
            ?? new Production.Models.Result();//Si no Existe creamos un registro nuevo del Modulo en el Turno Actual
            
            //Calculo de Tiempo Productivo
            if(result.InitialTime != DateTime.MinValue){
                //Agregamos el Inicio del Turno para el Tiempo Productivo
                if(result.InitialTime > shift.DateStart && result.InitialTime < shift.DateEnd){
                    result.ProductiveTime = DateTime.Now - result.InitialTime;
                }else{
                    result.ProductiveTime = result.Shift.DateEnd - result.InitialTime;
                }
            }

            //Calculamos Disponibilidad en Base al Tiempo Productivo y el Tiempo Disponible
            if(result.ProductiveTime != TimeSpan.Zero && result.AvailableTime != TimeSpan.Zero){
                result.Availability = result.ProductiveTime / result.AvailableTime;
            }
            //Cargamos Listado de Issues para el Tiempo Muerto
            List<Production.Models.ProdIssue> types = _context.Issues.Where(i => i.Status == true).ToList();

            //Si no existe registro de Produccion en el Modulo se crea
            if(result != null && result.Id == 0){
                //Completamos los datos necesarios para el nuevo registro
                result.Date = shift.DateStart;
                result.ResourceCode = module.ToUpper();
                result.ShiftId = shift.Id;
                //result.Shift = shift;
                _context.Results.Add(result);
                _context.SaveChanges();
            }
            
            //Registros de Labor del Modulo en el Turno Actual
            //result.Labor = _context.Labors.Where(l => l.ResultId == result.Id).ToList();
            
            //Metas del Modulo
            result.Goals = _context.Goals.Where(g => g.ResourceCode == result.ResourceCode ).ToList();

            //Asignamos datos del turno actual
            if(result.Shift == null){result.Shift = shift; }
            
            //Calculo de Eficiencia
            var init = result.Date;//Fecha de Inicio del Turno
            var end = init.AddHours(result.Shift.Hours+1);//Agregamos Horas Totales del Turno

            var flag1 = false;//Flag para Actualizacion de la Eficiencia

            if(result.HourByHour != null && result.HourByHour.Count > 0){
                //Recorremos las horas desde el inicio del turno
                while (init < end && init < DateTime.Now)
                {   //Recorremos hora por hora y validamos si existe el registro de Eficiencia
                    try{
                        if(!result.HourByHour.Any(h => h.Hour.Date == init.Date && h.Hour.Hour == init.Hour))
                        {//Si no existe registro en la Hora generamos el registro
                            var thour = new Production.Models.HourByHour{
                                Hour = init,
                                Meta = result.Goals.FirstOrDefault(g => g.Hour.Hours == init.TimeOfDay.Hours).Qty,//Cantidad Meta en esa Hora
                                ResultId = result.Id ,//Id de Registro
                                ResourceCode = result.ResourceCode //Modulo
                            };
                            result.HourByHour.Add(thour);//Agregamos el nuevo registro de Eficiencia
                            flag1 = true;//Flag para Actualizar
                        }
                        init = init.AddHours(1);//Aumentamos la Hora para el recorrido
                    }catch(System.NullReferenceException ex){}
                }
                result.HourByHour.OrderBy(h => h.Hour);//Ordenamos los Horarios
            }
            
            //Calculo de Eficiencia
            List<DJO.Models.EfficiencyHrs> _eficiencyList = _context.EfficiencyHrs.Where(e => e.ResultId == result.Id).OrderBy(e => e.Date).ToList();
            result.Eficiency = 0;
            if(_eficiencyList != null && _eficiencyList.Count > 0){
                foreach (var item in _eficiencyList)
                {
                    item.EmployeesQty = result.Labor.Where(l => l.Start.TimeOfDay.Hours <= item.Date.TimeOfDay.Hours && l.TypeId == 0 && (l.End == DateTime.MinValue || l.End.Hour == DateTime.Now.Hour)).GroupBy(l=> l.EmployeeNumber).Count();
                    item.PaidHrs = (item.EmployeesQty >0 )? item.EmployeesQty :0;
                    _context.EfficiencyHrs.Update(item);
                }

                result.Actual = _eficiencyList.Sum(e => e.Pieces);
                if(_eficiencyList.Sum(e => e.GainedHrs) > 0 && _eficiencyList.Sum(e=> e.PaidHrs) > 0){
                    //result.ProductiveTime = TimeSpan.FromHours( _eficiencyList.Sum(e => e.GainedHrs) );
                    result.Eficiency = _eficiencyList.Sum(e => e.GainedHrs) / _eficiencyList.Sum(e=> e.PaidHrs);
                }

                //result.Rate = result.Actual/result.ProductiveTime.TotalHours;
            }

            // if(result.Downtime != null && result.Downtime.Count() > 0){
            //     //Sum Downtime
            //     double tDowntTimeOpen = result.Downtime.Where(d => d.ClosedDate != DateTime.MinValue).Sum(d => d.Transcurred.TotalHours);
            //     DateTime FirstDowntime = (result.Downtime.Where(d => d.ClosedDate == DateTime.MinValue).Count() > 0)? result.Downtime.Where(d => d.ClosedDate == DateTime.MinValue).Min(d => d.Created) : DateTime.MinValue;
            //     double TempDowntime = (FirstDowntime != null || FirstDowntime != DateTime.MinValue)? (DateTime.Now - FirstDowntime).TotalHours : 0;
            //     result.ScheduledOperatingTime = TimeSpan.FromHours( Math.Round( tDowntTimeOpen + TempDowntime,4));
            // }

            // if(result.Shift!= null){
            //     //tiempo Transcurrido en el Turno
            //     result.OperativeTime = (DateTime.Now - result.Shift.DateStart);
            // }
            
            // result.Availability = (result.ScheduledOperatingTime.TotalHours > 0 && result.OperativeTime.TotalHours >0)? result.ScheduledOperatingTime.TotalHours / result.OperativeTime.TotalHours : 1;
            
            result.FirstPassYield = 1;
            if(double.IsInfinity(result.Eficiency)){
                result.Eficiency = 0;
            }
            result.OEE = result.Availability * result.Eficiency * result.FirstPassYield;
            
            try{
                if(result.Id >0){
                    var exist = _context.Results.FirstOrDefault(d => d.Id == result.Id);
                    if(exist != null){ _context.Entry(exist).State = EntityState.Detached; }
                    _context.Results.Update(result);
                }else{
                    _context.Results.Add(result);
                }
                
                _context.SaveChanges();
            }catch(Microsoft.EntityFrameworkCore.DbUpdateException ex){}
            
            return result;
        }

        
        //Retorno del Turno en base al horario actual
        public Interno.HumanResource.Models.Catalog.Shift getShift()
        {   
            DateTime now = DateTime.Now;//.Date.AddHours(20);
            if(now.Hour >= 6 && now.TimeOfDay.TotalHours < 18.2)
            {
                return _production.Shift.FirstOrDefault(s => s.Id == 1);
            }
            return _production.Shift.FirstOrDefault(s => s.Id == 2);
        }

        public void ValidateEficiency(string Module, DateTime shiftStart)
        {
            var _goals = _context.Goals.Where(g => g.ResourceCode == Module);//Metas del Modulo
            var _labor = _context.Labors.Where(g => g.Result.ResourceCode == Module && g.Start >= shiftStart);//Registros de Labor en el Modulo y la fecha
            //Regsitros del Eficiencia en el Modulo y la fecha
            List<DJO.Models.EfficiencyHrs> _efi = _context.EfficiencyHrs.Include(e => e.Resource).Where(e => e.Date >= shiftStart && e.ResourceCode == Module).ToList();
            //Fecha Inicial
            TimeSpan tempInit = shiftStart.TimeOfDay;
            //Recorremos mientras no sea la hora actual
            while (tempInit.Hours < TimeSpan.FromHours(DateTime.Now.TimeOfDay.Hours).Hours)
            {
                //Cargamos las Metas de la Hora actual en el Modulo
                var goal = _goals.FirstOrDefault(g => g.Hour.Hours == tempInit.Hours);
                //Empleados en la Hora actiul en el modulo
                var emp = _labor.Where(l=> (l.End.Hour == tempInit.Hours || l.End == DateTime.MinValue) && l.TypeId == 0).ToList();
                
                //Hora Temporal del Modulo para el calculo por Hora
                var tHour = _efi.FirstOrDefault(h => h.Hour == tempInit.Hours) ?? new Interno.DJO.Models.EfficiencyHrs{
                    Date = DateTime.Now.Date.AddHours(tempInit.TotalHours),//Fecha Actual con la Hora a revisar desde el inicio del turno
                    ResultId = _efi.First().ResultId,
                    Meta = (goal != null)? goal.Qty : 0,//Meta del Modulo en la hora revisada
                    EmployeesQty = (emp != null)? emp.Count() : 0,//Numero de empleados en la Hora revisada
                    StdTime = 0,
                    ResourceCode = Module,//Datos del Modulo
                };
                if(tHour.StdTime == 0 && tHour.Id ==0){//Si no existe registro de la Hora revisada agregamos ala base de datos
                    _context.EfficiencyHrs.Add(tHour);
                    _context.SaveChanges();
                }
                tempInit = TimeSpan.FromHours(tempInit.Hours +1);
            }
        }

        //INTERFACES PARA FORMULARIOS DEL MODULO
        public class IModuleSupervisor //Formalario de Supervisor
        {
            public DateTime Date { get; set; }
            public string Module { get; set; }
        }

        public class IDowntime : Production.Models.Downtime //Formulario de Downtime
        {
            [Required]
            public string Employee { get; set; }
            [Required]
            public string Module { get; set; }
        }

        public class IResultSet //Formulario de Conteo de Piezas
        {
            [Required]
            public string Module { get; set; }
            public string SubResource { get; set; }
            [Required]
            public string Employee { get; set; }
            [Required]
            public string Scan { get; set; }
            [Required]
            public int ResultId { get; set; }
        }

        public class ILabor //Formulario de Labor (Personal)
        {
            [Required]
            public string Employee { get; set; }
            [Required]
            public string Module { get; set; }
            [Required]
            public int Type { get; set; }
        }

        public class IEficiencia{ //Calculo de Grafica
            public int Acumulado { get; set; }
            public int RealAcumulado { get; set; }
            public double Eficiencia { get; set; }
        }
    }
}