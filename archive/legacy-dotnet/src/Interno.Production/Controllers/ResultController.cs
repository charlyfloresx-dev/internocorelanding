using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Interno.Production.Models;

namespace Interno.Production.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class ResultController : ControllerBase
    {
        private readonly ProductionContext _context;

        public ResultController(ProductionContext context)
        {
            _context = context;
        }

        // GET: api/Result
        [HttpGet]
        public async Task<ActionResult<IEnumerable<Result>>> GetResults()
        {
            return await _context.Results.OrderBy(r => r.Priority).ToListAsync();
        }

        // GET: api/Result/5
        [HttpGet("{id}")]
        public IActionResult GetResult(string id)
        {
            //Pendientes los Brakes
            //Agregar el tiempo disponible en planeacion
            var result = _context.Results.Include(r => r.Resource).Include(r => r.Shift).Where(r => r.ResourceCode == id && r.OrderQty > r.Actual).OrderBy(r => r.Priority).FirstOrDefault();
            return BadRequest();
        }

        [HttpPost("Available")]
        public IActionResult GetAvailableTime(Result data)
        {

            var plan = _context.Results.Include(r => r.Shift).Where(r => r.Date.Date == data.Date.Date && r.ResourceCode == data.ResourceCode && r.ShiftId == data.ShiftId).ToList();
            var shift = _context.Shift.FirstOrDefault(s => s.Id == data.ShiftId);
            foreach (var item in plan)
            {
                data.Shift = item.Shift;
                item.OperationTime = _context.OperationTime.FirstOrDefault(o => o.Product == item.Item);
                item.PlanedTime = (item.OperationTime != null) ? item.PlanQty * item.OperationTime.SetTime : TimeSpan.Zero;
            }
            shift.AvailableTime = shift.TotalTimeWorkday - shift.TotalTimeBreaks;
            return Ok(new
            {
                Shift = shift,
                Planed = plan.Sum(r => r.PlanedTime.TotalHours),
                Available = shift.AvailableTime.TotalHours - plan.Sum(r => r.PlanedTime.TotalHours),
                Plan = plan
            });
        }


        [HttpGet("Graphic/{code}")]
        public IActionResult GetGraphic(string code)
        {
            //1 --- Horarios del Turno
            var date = DateTime.Now.Date;
            //Turno
            Interno.HumanResource.Models.Catalog.Shift shift;
            //Datos del Recurso
            Interno.Production.Models.Resource resource = _context.Resource.FirstOrDefault(r => r.Code == code);
            if (resource != null)
            {
                //Validar los Turnos IMPORTANTISIMO
                if (DateTime.Now.Hour > 5 && DateTime.Now.Hour < 17)
                {
                    shift = this.GetShift(1);
                }
                else shift = this.GetShift(2);
                //Cargar datos en la Grafica
                var Graphic = this.GetGraphic(shift, resource, date);

                return Ok(Graphic);
            }
            ModelState.AddModelError("Resource", "El codigo del recurso no existe");
            return BadRequest(ModelState);
        }

        [HttpGet("Dashboard")]
        public IActionResult GetProductionDashboard()
        {
            var now = DateTime.Now;
            Interno.HumanResource.Models.Catalog.Shift shift;
            if (DateTime.Now.Hour > 4 && DateTime.Now.Hour < 17)
            {
                shift = this.GetShift(1);
            }
            else shift = this.GetShift(2);

            List<Result> results = _context.Results.Include(r => r.Resource).Include(r => r.Resource.BreakGroup).Where(r => r.Date.Date == now.Date).ToList();

            List<ResourceGraphic> list = new List<ResourceGraphic>();

            foreach (var item in results)
            {
                list.Add(this.GetGraphic(shift, item.Resource, now.Date));
            }

            return Ok(list);
        }

        protected ResourceGraphic getGraphicResource(Interno.Production.Models.Result result)
        {
            return this.GetGraphic(result.Shift, result.Resource, result.Date);
        }


        private ResourceGraphic GetGraphic(Interno.HumanResource.Models.Catalog.Shift shift, Resource resource, DateTime date)
        {
            ResourceGraphic graphic = new ResourceGraphic();
            var initialHour = shift.Start.Hours;//Horario Inicial
            date = date.AddHours(initialHour);//Fecha con Horario Inicial

            //Listado de Horarios para Grafica
            for (int i = 0; i < Math.Ceiling(shift.AvailableTime.TotalHours); i++) graphic.hours.Add(date.AddHours(i).TimeOfDay);

            //Inicializar Grafica

            foreach (var item in graphic.hours)
            {
                graphic.Disponible.Add(1);//Hora completa disponible
                graphic.Meta.Add(0);
                graphic.Producidas.Add(0);
                graphic.Faltante.Add(0);
                graphic.Excedente.Add(0);
                graphic.Real.Add(0);
                graphic.Eficiencia.Add(0);
            }
            //2 --- Descanzos
            //Cargar las metas de la estacion los PLanes de Produccion
            graphic.Plan = _context.Results.Include(r => r.HourByHour).Include(r => r.Shift).Where(r => r.Date.Date == DateTime.Now.Date && r.ResourceCode == resource.Code).Include(r => r.Breaks.Breaks).OrderBy(r => r.Priority).ToList();

            if (graphic.Plan.Count > 0)
            {
                //Agrupamos lo descanzos
                graphic.Breaks = graphic.Plan.GroupBy(p => p.Breaks.Breaks).Select(p => p.Key).First();
                //Calculo de tiempo DISPONIBLE SEGUN DESCANZOS
                foreach (var item in graphic.Breaks)
                {
                    var StartH = item.Start.Hours;
                    var EndH = item.End.Hours;
                    for (int i = 0; i < graphic.hours.Count; i++)
                    {
                        if (graphic.hours[i].Hours == StartH)
                        {
                            graphic.Disponible[i] = item.Start.TotalHours - graphic.hours[i].TotalHours;
                        }
                        if (graphic.hours[i].Hours == EndH)
                        {
                            graphic.Disponible[i] = graphic.hours[i + 1].TotalHours - item.End.TotalHours;
                        }
                    }
                }
                //Agregamos Termino e Inicio del Turno al Listado de Tiempo Disponible
                if (shift.End.Minutes != 0) { graphic.Disponible[graphic.Disponible.Count - 1] = (shift.End - graphic.hours[graphic.hours.Count - 1]).TotalHours; }

                if (shift.Start.Minutes != 0) { graphic.Disponible[0] = (graphic.hours[1] - shift.Start).TotalHours; }
                //Agregamos el Tiempo Disponible
                foreach (var item in graphic.Disponible) graphic.Horas.Add(TimeSpan.FromHours(item));
                //Tiempo del Turno 
                var totalBreaks = TimeSpan.FromHours(graphic.Breaks.Sum(b => b.Duration.TotalHours));//Calculamos total de tiempo en Descanzos
                var tiempoDisponible = graphic.Disponible.Sum(); //Cantidas en Horas Disponibles
                TimeSpan tDisponible = TimeSpan.Zero;
                foreach (var item in graphic.Horas) tDisponible = tDisponible + item;//Sumamos cada una de las horas para calcular el tiempo disponible
                tDisponible = tDisponible + totalBreaks;//Le restamos los Descanzos

                //return Ok(new{hours,Disponible,Horas,tDisponible,totalBreaks });
                //3 Plan de Produccion y Metas
                //Creacion de Metas
                int con = 0;//Posicion de las horas en la Grafica
                double qtyPlan = 0;//Almacena Cantidad del Plan

                foreach (var item in graphic.Plan)
                {
                    double necesary = item.AvailableTime.TotalHours;//Tiempo Planeado de Operacion
                    qtyPlan = item.PlanQty;//Cantidad Planead
                    double qtyPerHour = 0;
                    item.OperationTime = _context.OperationTime.FirstOrDefault(ot => ot.Product == item.Item);

                    if (con != 0) { con--; }
                    while (qtyPlan > 0 && con < graphic.Disponible.Count)
                    {

                        if (item.OperationTime != null)
                        {
                            item.PlanedTime = item.PlanQty * item.OperationTime.SetTime;
                            Console.WriteLine("{0},{1},{2}", graphic.Horas[con], item.OperationTime.SetTime, graphic.Horas[con] / item.OperationTime.SetTime);
                            qtyPerHour = Math.Floor(graphic.Horas[con] / item.OperationTime.SetTime);
                        }
                        else
                        {
                            //Arreglar distribucion de las Horas
                            qtyPerHour = Math.Round(item.PlanQty / necesary);
                        }

                        graphic.Meta[con] = qtyPerHour;//Fijar Meta por Hora
                        graphic.Faltante[con] = Int16.Parse(graphic.Meta[con].ToString());
                        qtyPlan = qtyPlan - qtyPerHour;
                        con++;
                    }
                }
                var results = _context.HourByHour.Where(r => r.ResourceCode == resource.Code && r.Hour.Date == date.Date).GroupBy(h => h.Hour.Hour).Select(h => new { Hour = TimeSpan.FromHours(h.Key), Meta = h.Sum(r => r.Meta), Producidas = h.Sum(r => r.Pieces) }).ToList();

                foreach (var item in results)
                {//Buscamos el horario de la Grafica
                    if (item.Hour.Hours <= DateTime.Now.Hour)
                    {
                        var index = graphic.hours.IndexOf(item.Hour);
                        //Si existe el horario en la Grafica
                        if (index != -1)
                        {
                            graphic.Real[index] = item.Producidas;
                            if (graphic.Real[index] > graphic.Meta[index])
                            {
                                graphic.Excedente[index] = graphic.Real[index] - Int16.Parse(graphic.Meta[index].ToString());
                                graphic.Faltante[index] = 0;
                                graphic.Producidas[index] = Int16.Parse(graphic.Meta[index].ToString());
                            }
                            else
                            {
                                graphic.Faltante[index] = Int16.Parse(graphic.Meta[index].ToString()) - graphic.Real[index];
                                graphic.Producidas[index] = graphic.Real[index];
                            }
                        }
                    }
                }
                //Calculo de Eficiencia
                for (int i = 0; i < graphic.Meta.Count; i++)
                {
                    if (graphic.Producidas[i] != 0) graphic.Eficiencia[i] = Int16.Parse(Math.Ceiling((graphic.Producidas[i] * 100) / graphic.Meta[i]).ToString());
                }
                return graphic;
            }
            return graphic;
        }

        // PUT: api/Result/5
        // To protect from overposting attacks, enable the specific properties you want to bind to, for
        // more details, see https://go.microsoft.com/fwlink/?linkid=2123754.
        [HttpPut("{id}")]
        public async Task<IActionResult> PutResult(int id, Result result)
        {
            if (id != result.Id)
            {
                return BadRequest();
            }

            _context.Entry(result).State = EntityState.Modified;

            try
            {
                await _context.SaveChangesAsync();
            }
            catch (DbUpdateConcurrencyException)
            {
                if (!ResultExists(id))
                {
                    return NotFound();
                }
                else
                {
                    throw;
                }
            }

            return NoContent();
        }

        // POST: api/Result
        // To protect from overposting attacks, enable the specific properties you want to bind to, for
        // more details, see https://go.microsoft.com/fwlink/?linkid=2123754.
        [HttpPost]
        public IActionResult PostResult(Result result)
        {
            if (result.Date == DateTime.MinValue) ModelState.AddModelError("Date", "Plan Date is required");
            if (result.Priority == 0) ModelState.AddModelError("Priority", "Priority number is required");
            if (result.WorkOrder == null) ModelState.AddModelError("WorkOrder", "Work Order is required");
            if (result.OrderQty == 0) ModelState.AddModelError("OrderQty", "Order Qty is required");
            if (result.PlanQty == 0) ModelState.AddModelError("PlanQty", "Plan Qty is required");
            if (result.Operators == 0) ModelState.AddModelError("Operators", "Head Count is required");
            if (result.ShippingDate == DateTime.MinValue) ModelState.AddModelError("ShippingDate", "Shipping Date is required");
            if (result.WHSDate == DateTime.MinValue) ModelState.AddModelError("WHSDate", "WHS Date is required");
            if (result.SMKTDate == DateTime.MinValue) ModelState.AddModelError("SMKTDate", "SMKT Date is required");
            if (ModelState.IsValid)
            {
                if (result.ShiftId != 0)
                {
                    result.Shift = this.GetShift(result.ShiftId);//Tiempo disponible del Turno
                    //Restarle el descanzo al tiempo disponible del turno
                    var Resource = _context.Resource.Include(r => r.BreakGroup).Include(r => r.BreakGroup.Breaks).FirstOrDefault(r => r.Code == result.ResourceCode);
                    if (Resource != null)
                    {
                        result.Resource = Resource;
                        result.Breaks = _context.breaksGroups.FirstOrDefault(g => g.Id == result.Resource.BreakGroup.Id);
                        _context.Results.Add(result);
                        if (_context.SaveChanges() > 0)
                        {
                            return CreatedAtAction("GetAvailableTime", new { result });
                        }
                    }
                    else ModelState.AddModelError("Resource", "Resource Code is required or not valid.");
                }
                else ModelState.AddModelError("ShiftId", "Shift Id is required");
            }
            return BadRequest(ModelState);
        }

        private Interno.HumanResource.Models.Catalog.Shift GetShift(int Id)
        {
            var shift = _context.Shift.FirstOrDefault(s => s.Id == Id);
            shift.AvailableTime = shift.TotalTimeWorkday - shift.TotalTimeBreaks;
            return shift;
        }

        // DELETE: api/Result/5
        [HttpDelete("{id}")]
        public async Task<ActionResult<Result>> DeleteResult(int id)
        {
            var result = await _context.Results.FindAsync(id);
            if (result == null) return NotFound();
            _context.Results.Remove(result);
            await _context.SaveChangesAsync();
            return result;
        }

        private bool ResultExists(int id) => _context.Results.Any(e => e.Id == id);

        private List<TimeSpan> getGraphicHours(Interno.HumanResource.Models.Catalog.Shift shift)
        {
            //Fecha y Turno Actual
            var now = DateTime.Now;
            List<TimeSpan> hours = new List<TimeSpan>();
            if (shift == null)
            {
                shift = _context.Shift.FirstOrDefault(s => now.TimeOfDay >= s.Start && now.TimeOfDay <= s.End);
            }
            //Test Night
            //shift.Start = TimeSpan.FromHours(16);
            //shift.End = TimeSpan.FromHours(1);
            //Generamos Horarios segun el turno
            if (shift.End.Hours == 16)
            {
                for (int i = shift.Start.Hours; i < shift.End.Hours + 1; i++) hours.Add(TimeSpan.FromHours(i));
            }
            else
            {
                for (int i = shift.Start.Hours; i < 24; i++) hours.Add(TimeSpan.FromHours(i));
                for (int i = 0; i < shift.End.Hours; i++) hours.Add(TimeSpan.FromHours(i));
            }
            return hours;
        }
    }
}
