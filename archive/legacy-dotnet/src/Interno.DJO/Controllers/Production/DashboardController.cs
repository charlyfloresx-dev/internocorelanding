using System;
using System.Data;
using System.Collections.Generic;
using System.Linq;

using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

using System.ComponentModel.DataAnnotations;
using Interno.Production.Models;

namespace Interno.DJO.Models
{
    [ApiController]
    [Route("[Controller]")]
    public class DashboardController : ControllerBase
    {
        private readonly Interno.DJO.DJOContext _context;
        private readonly Interno.Production.Models.ProductionContext _production;

        public DashboardController(Interno.DJO.DJOContext contex, ProductionContext production)
        {
            _context = contex;
            _production = production;
        }

        [HttpGetAttribute("Calculate")]
        public IActionResult calculateEficiency()
        {
            DJO.Controllers.ModuleController _module = new Controllers.ModuleController(_context,_production);
            var shift = _module.getShift();
            //Cargamos Listado de Hora por Hora de Eficiencia
            List<DJO.Models.EfficiencyHrs> _efi = _context.EfficiencyHrs.Include(e => e.Resource).Where(e => e.Date >= shift.DateStart && e.Date <= shift.DateEnd).ToList();
            //Agrupamos Registros de Eficiencia por Modulo
            List<string> modules = _efi.GroupBy(g => g.ResourceCode).Select(s => s.Key).ToList();
            
            List<Interno.Production.Models.Goal> _goals =_context.Goals.ToList();//Cargamos las metas de los Modulos
            //Cargamos los registros de Labor para contar los empleados al momento del calculo en el Modulo
            List<Interno.Production.Models.Labor> _labor = _context.Labors.Include(l => l.Result).Include(l => l.Result.HourByHour).Where(l => l.Start >= shift.DateStart && l.TypeId == 0).ToList();
            
            var updated = 0;//Contador de Actualizacione en el Sistema
            //Recorremos los modulos para el calculo de su Eficiencia
            foreach (var item in _efi.GroupBy(e => e.ResourceCode))
            {
                //Fecha Inicial
                TimeSpan tempInit = shift.Start;
                //Recorremos mientras no sea la hora actual
                while (tempInit.Hours < TimeSpan.FromHours(DateTime.Now.TimeOfDay.Hours).Hours)
                {
                    //Cargamos las Metas de la Hora actual en el Modulo
                    var goal = _goals.FirstOrDefault(g => g.ResourceCode == item.Key && g.Hour.Hours == tempInit.Hours);
                    //Empleados en la Hora actiul en el modulo
                    var emp = _labor.Where(l=> (l.End.Hour == tempInit.Hours || l.End == DateTime.MinValue) && l.TypeId == 0 && l.ResultId == item.First().ResultId ).ToList();
                    
                    //Hora Temporal del Modulo para el calculo por Hora
                    var tHour = item.FirstOrDefault(h => h.Hour == tempInit.Hours) ?? new EfficiencyHrs{
                        Date = DateTime.Now.Date.AddHours(tempInit.TotalHours),//Fecha Actual con la Hora a revisar desde el inicio del turno
                        ResultId = item.First().ResultId,
                        Meta = (goal != null)? goal.Qty : 0,//Meta del Modulo en la hora revisada
                        EmployeesQty = (emp != null)? emp.Count() : 0,//Numero de empleados en la Hora revisada
                        StdTime = 0,
                        ResourceCode = item.First().ResourceCode,//Datos del Modulo
                    };
                    if(tHour.StdTime == 0 && tHour.Id ==0){//Si no existe registro de la Hora revisada agregamos ala base de datos.
                        _context.EfficiencyHrs.Add(tHour);
                    }
                    tempInit = TimeSpan.FromHours(tempInit.Hours +1);
                }
                updated += _context.SaveChanges();
            }
            //Cargamos los registros de cada modulo, su Hora por hora y Labor
            List<Interno.Production.Models.Result> _results = _context.Results.Include(r => r.HourByHour).Include(r => r.Labor).Where(l => l.Date >= shift.DateStart && l.Date <= shift.DateEnd.AddHours(0.25) && l.Labor.Count() > 0 && l.HourByHour.Count() == 0).ToList();
            
            foreach (var item in _results.GroupBy(e => e.ResourceCode).Select( s => s.FirstOrDefault()))
            {
                if(item.HourByHour.Count() == 0){//Si el Modulo no tiene produccion pero tiene registrados operadores
                    
                    //Fecha Inicial
                    TimeSpan tempInit = shift.Start;
                    //Metas del Modulo
                    item.Goals = _goals.Where(g => g.ResourceCode == item.ResourceCode).ToList();
                    //Recorremos mientras no sea la hora actual
                    while (tempInit.Hours < TimeSpan.FromHours(DateTime.Now.TimeOfDay.Hours).Hours)
                    {
                        var emp = item.Labor.Where(l=> (l.End.Hour == tempInit.Hours || l.End == DateTime.MinValue) && l.TypeId == 0);
                        var goalHour = item.Goals.FirstOrDefault(g => g.ResourceCode == item.ResourceCode && g.Hour.Hours == tempInit.Hours);
                        //Calculo de Hora por Hora
                        var tHour = _efi.FirstOrDefault(h => h.Hour == tempInit.Hours && h.ResultId == item.Id) ?? new EfficiencyHrs{
                            Date = DateTime.Now.Date.AddHours(tempInit.TotalHours),//Fecha Actual con la Hora a revisar desde el inicio del turno
                            ResultId = item.Id,
                            Meta = (goalHour != null)? goalHour.Qty : 0,//Meta del Modulo en la hora revisada
                            EmployeesQty = (emp != null)? emp.Count() : 0,//Numero de empleados en la Hora revisada
                            StdTime = 0,
                            ResourceCode = item.ResourceCode,//Datos del Modulo
                        };
                        if(tHour.StdTime == 0 && tHour.Id ==0){//Si no existe registro de la Hora revisada agregamos ala base de datos.
                            _context.EfficiencyHrs.Add(tHour);
                        }
                        tempInit = TimeSpan.FromHours(tempInit.Hours +1);
                    }
                    updated += _context.SaveChanges();
                }
                
            }
            return Ok(updated);
        }

        [HttpGet("Efficiency")]
        public IActionResult getEficiencyDashboard()
        {
            //Referencia al Controlador Modulos
            DJO.Controllers.ModuleController _module = new Controllers.ModuleController(_context,_production);
            var shift = _module.getShift();//Turno actual

            List<Interno.Production.Models.Goal> _goals =_context.Goals.ToList();//Cargamos metas de los Modulos
            
            // //this.calculateEficiency();//Calculamos la Eficiencia de los Modulos y actualizamos los datos

            
            //List<Interno.Production.Models.Resource> whs = _context.Resources.ToList();//Cargamos la Informacion de los Recursos (Modulos)
            // List<Interno.Production.Models.Result> _results = _context.Results.Include(r => r.Downtime).Include(r => r.Labor).Where(r => r.Date >= shift.DateStart).ToList();
            // List<int> _ids = _results.Select(r => r.Id).ToList();
            // List<Interno.DJO.Models.EfficiencyHrs> _efi = _context.EfficiencyHrs.Where(e =>  _ids.Contains(e.ResultId)).ToList();
            // foreach (var item in _efi)
            // {
            //     item.EmployeesQty = _results.FirstOrDefault(r => r.Id == item.ResultId)
            //                                 .Labor.Where(l => l.Start.TimeOfDay.Hours <= item.Date.TimeOfDay.Hours && l.TypeId == 0 && (l.End == DateTime.MinValue || l.End.Hour == DateTime.Now.Hour))
            //                                 .GroupBy(l=> l.EmployeeNumber).Count();
            //     item.PaidHrs = (item.EmployeesQty > 0 )? item.EmployeesQty : 0;
            //     _context.EfficiencyHrs.Update(item);
            // }

            // foreach (var item in _results.Where(r => r.ResourceCode == "M-77"))
            // {
            //     item.Operators = item.Labor.GroupBy(e => e.EmployeeNumber).Count();
            //     item.Capacity = _efi.Where(e => e.ResultId == item.Id).GroupBy(e => e.Date).Select(e => e.FirstOrDefault()).Sum(e => e.PaidHrs);
            //     item.Inprovement = _efi.Where(e => e.ResultId == item.Id).GroupBy(e => e.Date).Select(e => e.FirstOrDefault()).Sum(e => e.GainedHrs);
            //     item.PlanQty = _efi.Where(e => e.ResultId == item.Id).GroupBy(e => e.Date).Select(e => e.FirstOrDefault()).Sum(e => e.Meta);
            //     item.Actual = _efi.Where(e => e.ResultId == item.Id).Sum(e => e.Pieces);
            //     var temp = item.Downtime.OrderBy(d => d.Created).FirstOrDefault(d => d.ClosedDate == DateTime.MinValue);
            //     item.Date1 = (temp != null)? temp.Created : DateTime.MinValue;
            //     item.Shift = shift;
            //     foreach (var efi in _efi.Where(e => e.ResourceCode == item.ResourceCode))
            //     {
            //         item.ProductiveTime += TimeSpan.FromHours(efi.Pieces*efi.StdTime);
            //         EfficiencyHrs tEfi = new EfficiencyHrs();
            //     }
            //     return Ok(item);
            // }
            // return BadRequest();

            // return Ok(_efi.Where(e => e.ResourceCode == "M-77").OrderBy(e => e.Date).GroupBy(e => e.Date.Hour).Select(e => new EfficiencyHrs{
            //     ResourceCode = e.Last().ResourceCode,
            //     Date = e.Last().Date,
            //     ResultId = e.Last().ResultId,
            //     StdTime = e.Average(e => e.StdTime),
            //     Meta = e.Last().Meta,
            //     Pieces = e.Sum(e => e.Pieces),
            //     EmployeesQty = e.Last().EmployeesQty,
            //     PaidHrs = e.Last().PaidHrs,
            // }));

            //List<Interno.Production.Models.Result> _results = new List<Result>();
            // List<Interno.Production.Models.Resource> _resources = _context.Resources.ToList();
            // DJO.Controllers.ModuleController _module = new Controllers.ModuleController(_context,_production);

            // foreach (var item in _resources)
            // {
            //     _results.Add(_module.getModuleNowResult(item.Code));
            // }




            //Sin Calculo de OEE
            List<Interno.Production.Models.Result> _results = _context.Results.Where(r => r.Date.Date == DateTime.Now.Date && r.ShiftId == shift.Id).ToList();
            
            //Registros de Labor en el Turno
            List<Interno.Production.Models.Labor> _labor = _context.Labors.Include(l => l.Result).Where(l => l.Start >= shift.DateStart && l.TypeId == 0).ToList();
            //Registros de Eficiencia en el Turno
            List<DJO.Models.EfficiencyHrs> _efi = _context.EfficiencyHrs.Include(e => e.Resource).Where(e => e.Date >= shift.DateStart && e.Date <= shift.DateEnd).ToList();

            
            //Cargamos los registros de Tiempo Muerto Pendientes
            List<Interno.Production.Models.Downtime> _downtime = _context.Downtimes.Include(d => d.Result).Where(d => d.Created > shift.DateStart || d.ClosedDate ==  DateTime.MinValue).ToList();
            // return Ok(new{
            //     Issues =_downtime.Count(),
            //     LastShift = _downtime.Where(d => d.Created <= shift.DateStart).Count(),
            //     Closed = _downtime.Where(d => d.ClosedDate != DateTime.MinValue).Count(),
            //     _downtime
            // });
            //Agrupadmos Downtime por Modulo y Contamos los registros
            var _dow=  _context.Downtimes.Include(d => d.Result).Where(d => d.Created > shift.DateStart ).GroupBy(d => d.Result.ResourceCode).Select(s => new{
                s.Key,
                Count = s.Count()
            }).ToList();
            //Agrupamos el Downtime por Modulo y Cargamos la Fecha mas antigua de los registros aun abiertos
            var trans = _context.Downtimes.Include(d => d.Result).Where(d => d.Created > shift.DateStart.AddMonths(-1) && d.ClosedDate == DateTime.MinValue ).GroupBy(d => d.Result.ResourceCode).Select(s => new{
                s.Key,
                Created = s.Min(r => r.Created)
            }).ToList();
            
            //Updated Data Efifiency
            //Cargamos los registros de Eficiencia Actualaes con las Informaciond el Recurso (Modulo)
            _efi = _context.EfficiencyHrs.Include(e => e.Resource).Where(e => e.Date >= shift.DateStart).OrderBy(r => r.Date).ToList();
            
            List<DJO.Models.EfficiencyHrs> complete = new List<EfficiencyHrs>();//Listado de Eficiencia con todos los modulos y registros por hora para desplegar en el Dashboard
            //Agrupamos por Modulo y Hora la Eficiencia 
            var group = _efi.GroupBy(e => e.ResourceCode).Select(e => new{
                    Module = e.Key,
                    Hours = e.GroupBy(g => g.Date.Hour).Select(e => new{
                        Hour = e.Key,
                        Data = e 
                    }),
                    Resource = e.First().Resource
                });
            //Recorremos los Modulos
            foreach (var item in group)
            {
                double gain = 0;
                foreach (var hour in item.Hours)
                {
                        gain = hour.Data.First().GainedHrs;
                        EfficiencyHrs temp = new EfficiencyHrs();
                        temp.ResourceCode = item.Module;
                        temp.Date = shift.DateStart.Date.AddHours(hour.Hour);
                        temp.Meta = hour.Data.Sum(e => e.Meta);
                        temp.Pieces = hour.Data.Sum(h => h.Pieces);
                        temp.EmployeesQty = hour.Data.Sum(h => h.EmployeesQty);
                        temp.StdTime = hour.Data.Sum(h => h.GainedHrs)/hour.Data.Sum(h => h.Pieces);
                        temp.Resource = item.Resource;
                        complete.Add(temp);
                }
            }

            List<DJO.Models.EfficiencyHrs> individual = new List<EfficiencyHrs>();//Listado de Eficiencia por Modulo Actual

            foreach (var item in complete.GroupBy(g => g.ResourceCode))//Agrupamos por Recurso (Modulo)
            {
                //Calculamos la Eficiencia individual por cada Modulo
                EfficiencyHrs temp = new EfficiencyHrs();
                temp.ResourceCode = item.Key;//Codigo del Modulo
                temp.Date = item.First().Date.Date;
                //Meta en la Hora Actual
                var tgoal = _goals.Where(g => g.ResourceCode == item.Key && g.Hour >= shift.Start && g.Hour.TotalHours < DateTime.Now.TimeOfDay.TotalHours);
                temp.Meta = (tgoal != null)? tgoal.Sum(g => g.Qty) :0;
                temp.Pieces = item.Sum(e => e.Pieces);
                //Labor actual del Modulo
                var tLabor = _labor.Where(l => l.Result.ResourceCode == item.Key && (l.End == DateTime.MinValue || l.End.Hour == DateTime.Now.Hour)).GroupBy(g => g.EmployeeNumber).Select(s => new{s.Key,Hours = Math.Ceiling((DateTime.Now -  s.Min(m => m.Start)).TotalHours)});
                
                temp.EmployeesQty = (tLabor!=null)? tLabor.Count() : 0;
                temp.PaidHrs = (tLabor != null)? tLabor.Sum(l => l.Hours) :0;
                temp.StdTime = item.Sum(h => h.GainedHrs)/item.Sum(h => h.Pieces);
                temp.Resource = item.First().Resource;
                Interno.DJO.Controllers.ModuleController _modules = new Controllers.ModuleController(_context,_production);
                //temp.Result = _modules.getModuleNowResult(temp.ResourceCode);
                try{
                    //Tiempo Muerto actual en el Modulo
                    var dt = _dow.Where(d => d.Key == item.Key).ToList();
                    temp.Issues = (dt.Count() > 0)? dt.First().Count :0 ;
                    var tr = trans.OrderBy(t => t.Created).FirstOrDefault(d => d.Key == item.Key);
                    temp.Downtime = tr.Created;
                    temp.ProdIssueDowntime = tr;
                    
                }catch(System.NullReferenceException){  }
                
                individual.Add(temp);//Agregamos Eficiencia Actual del Modulo al Listado para desplegar en el dashboard
            }
            return Ok(new{
                individual = individual.OrderBy(r => r.Eficiency),//Eficiencia por Modulo
                complete,//Todos las Datos de Eficiencia
                eficiency = _efi,//Calculo de Eficiencia General
                value = complete.GroupBy(r => r.Resource.Description).Select(r => r.Key).ToList()//Datos Aggrupador por Modulo
                });
        }

        [HttpGet("Downtime/Trend")]
        public IActionResult getDowntimeTrend()
        {
            var now = DateTime.Now.Date;
            List<Interno.Production.Models.Downtime> downtime = _context.Downtimes.Include(i => i.Issue).Include(r => r.Result).Where(d => d.Created.Date >= now.AddDays(-30)).ToList();
            var group = downtime.GroupBy(d => d.Created.Date).Select(s => new{ s.Key, Value = s.Sum(s => s.Transcurred.TotalHours)}).OrderBy(r => r.Key).ToList();
            
            //TREND
            List<DateTime> dates = new List<DateTime>();
            List<string> categories = new List<string>();
            List<decimal> series = new List<decimal>();
            
            for (int i = 30; i > 0; i--)
            {
                dates.Add(now.AddDays(-i));
                categories.Add(now.AddDays(-i).Date.ToString("MM-dd"));
                series.Add(0);
            }

            //Create Trend
            for (int i = 0; i < group.Count(); i++)
            {
                var index = categories.IndexOf(group[i].Key.Date.ToString("MM-dd"));
                
                if(index != -1){
                    series[index] = Decimal.Round( Decimal.Parse(group[i].Value.ToString()),2);
                }
                
                
            }

            //PARETO Modules
            var groupP = downtime.GroupBy(d => d.Result.ResourceCode).Select(s => new{s.Key,Value = s.Sum(r => r.Transcurred.TotalHours)}).OrderByDescending(r => r.Value).Take(20).ToList();
            List<string> pcategories = new List<string>();
            List<decimal> pseries = new List<decimal>();
            foreach (var item in groupP)
            {
                pcategories.Add(item.Key);
                pseries.Add(Decimal.Round( Decimal.Parse(item.Value.ToString()),2));
            }
            //PARETO ISSUE
            var groupPI = downtime.GroupBy(d => d.Issue).Select(s => new{s.Key.Description,Value = s.Count()}).OrderByDescending(r => r.Value).Take(10).ToList();
            List<string> pIcategories = new List<string>();
            List<decimal> pIseries = new List<decimal>();

            foreach (var item in groupP)
            {
                pcategories.Add(item.Key);
                pseries.Add(Decimal.Round( Decimal.Parse(item.Value.ToString()),2));
            }
            foreach (var item in groupPI)
            {
                pIcategories.Add(item.Description);
                pIseries.Add(Decimal.Round( Decimal.Parse(item.Value.ToString()),2));
            }
            return Ok(new{ 
                Trend = new {categories,series},
                Pareto =  new {categories = pcategories, series = pseries},
                Pareto2 = new {categories = pIcategories, series = pIseries},
                dates,
                group,
                downtime
            });
        }

        
    }
}