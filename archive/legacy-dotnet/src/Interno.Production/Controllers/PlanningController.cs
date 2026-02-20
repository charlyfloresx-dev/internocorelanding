using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Interno.Production.Models;

using Microsoft.AspNetCore.Http;
using System.Data;
using ExcelDataReader;



namespace Interno.Production.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class PlanningController : ControllerBase
    {
        
        private readonly ProductionContext _production;
        private readonly Interno.HumanResource.Models.HRContext _hr;
        public PlanningController(ProductionContext context, Interno.HumanResource.Models.HRContext hr)
        {
            _production = context;
            _hr = hr;
        }

        [HttpGet("")]
        public IActionResult getWHSPlan()
        {
            var items = _production.OperationTime.ToList();
            var plan = _production.Plannings.Where(p => p.KitDate.Date <= DateTime.Now.AddDays(7) && p.KitDate != DateTime.MinValue).OrderBy(p => p.KitDate);
            foreach (var item in plan)
            {
                item.OperationTime = items.FirstOrDefault(i => i.Product == item.PartNumber);
            }
            return Ok(plan);
        }

        [HttpPost("WHS/Update")]
        public IActionResult setWHSUpdate(Planning data)
        {
            data.WHSUpdate = DateTime.Now;
            _production.Plannings.Update(data);
            if(data.Status == Domain.Enum.StatusType.Complete){
                if(data.OperationTime.SetTime == TimeSpan.Zero || data.OperationTime.SetTime == TimeSpan.MinValue){
                    ModelState.AddModelError("OperationTime","Es necesario actualizar el tiempo de Operacion de "+data.PartNumber);
                }
                var emp = _hr.Employee.FirstOrDefault(e => e.Number == Interno.Domain.InternoExtensions.getNumber(data.Employee) && e.Active == true);
                
                if(emp == null){ ModelState.AddModelError("Employee","No existe registro del empleado o no es un empleado activo"); }
                
                if(ModelState.IsValid){
                    var shifts = _production.Shift.OrderBy(s => s.Id).Take(2).ToList();
                    WorkOrder order = _production.WorkOrders.FirstOrDefault(o => o.Id == data.Order);
                    if(order != null){
                        var results = _production.Results.Where(r => r.WorkOrder == order.Id).ToList();
                        var pendientes = results.Where(r => r.Date.Date < DateTime.Now.Date).GroupBy(r => r.Id).Select(r => (r.Sum(r => r.PlanQty) - r.Sum(r => r.Actual))).FirstOrDefault();
                        var planiadas = results.Where(r => r.Date.Date >= DateTime.Now.Date).GroupBy(r => r.Id).Select(r => r.Sum(r => r.PlanQty) - r.Sum(r => r.Actual)).FirstOrDefault();
                        //Producidas
                        order.ManufQty = results.Sum(r => r.Actual);
                        var Faltantes = order.OrderQty - order.ManufQty - planiadas;
                        return Ok(new{order.OrderQty,order.ManufQty,planiadas,Faltantes,order});
                        
                    }else ModelState.AddModelError("Order","No se encontro registro de la Orden");
                }
                return BadRequest(ModelState);
            }
            //Actualizamos estado de la Orden
            return Ok(_production.SaveChanges());
        }
        
        

        [HttpPost("Upload")]
        public IActionResult setPlanWarehouse([FromForm] IFormFile file)
        {
            //Si contiene archivos 
            if(file.Length > 0){
                //Lector de Documentos de Excel
                using (var reader = ExcelReaderFactory.CreateReader(file.OpenReadStream()))
                {
                    //Creamos el DataTable con los registros
                    var result = reader.AsDataSet(new ExcelDataSetConfiguration()
                    {
                        ConfigureDataTable = (_) => new ExcelDataTableConfiguration()
                        { UseHeaderRow = true }
                    });
                    var item = _production.OperationTime.ToList();
                    var ordenes = _production.WorkOrders.ToList();     
                    var resources = _production.Resource.ToList(); 
                    var breaks = _production.breaksGroups.Include(b => b.Breaks).ToList();     
                    DataTable dt = result.Tables[0];
                    
                    
                    for (int i = 2; i < dt.Rows.Count; i++)
                    {
                        /* ----- Planeacion de Almacen ------ */
                        int orderQty;
                        bool order = Int32.TryParse(dt.Rows[i][6].ToString(), out orderQty);
                        DateTime shipping;
                        bool ship = DateTime.TryParse(dt.Rows[i][9].ToString(),out shipping);
                        DateTime kitDate;
                        bool kit = DateTime.TryParse(dt.Rows[i][82].ToString(),out kitDate);
                        
                        if(order && ship && kit){
                            Planning plan = new Planning();
                            plan.Line = dt.Rows[i][0].ToString();
                            plan.PartNumber = dt.Rows[i][3].ToString();
                            plan.Order = dt.Rows[i][5].ToString();
                            plan.OrderQty = orderQty;
                            plan.ShippingDate = shipping;
                            plan.SO = dt.Rows[i][77].ToString();
                            plan.SOLine = dt.Rows[i][78].ToString();
                            plan.PO = dt.Rows[i][79].ToString();
                            plan.altBOM = dt.Rows[i][80].ToString();
                            plan.KitDate = kitDate;
                            plan.Comments = dt.Rows[i][88].ToString();
                            plan.Comments2 = dt.Rows[i][89].ToString();
                            _production.Plannings.Add(plan);
                        }
                        /* ----- Planeacion de Almacen ------ */

                        /* ----- Planeacion de Produccion ------ */
                        
                        DateTime date;
                        bool fecha = DateTime.TryParse(dt.Rows[0][17].ToString(),out date);
                        short op;
                        bool ope = Int16.TryParse(dt.Rows[i][1].ToString(),out op);
                        string  product = dt.Rows[i][3].ToString();
                        bool exist = item.Any(i => i.Product == product);
                        //bool wo = ordenes.Any(w => w.Id == dt.Rows[i][5].ToString());
                        //Console.WriteLine(new{i,wo,,date,op,exist,Item = dt.Rows[i][3].ToString()});
                        /*
                        if(wo){
                          */  
                            
                            if(fecha && op != 0  && ship && kit){
                                
                                for (int col = 10; col < 66; col = col +12)
                                {
                                    
                                    int qty;
                                    bool plan = Int32.TryParse(dt.Rows[i][col].ToString(),out qty);
                                    
                                    if(plan && qty !=0){ //Turno 1
                                        Result res = new Result();
                                        res.Priority = 1;
                                        res.Date = date;
                                        res.Resource = resources.FirstOrDefault(r => r.Code == dt.Rows[i][0].ToString());
                                        
                                        if(res.Resource != null){
                                            Console.WriteLine(new{ i, date,ope,product,exist,shipping,kitDate,qty,Code = res.Resource.Code });
                                            //Turno Segun Columna
                                            res.Operators = op;
                                            res.Item = dt.Rows[i][3].ToString();
                                            res.WorkOrder = dt.Rows[i][5].ToString();
                                            res.OrderQty = orderQty;
                                            res.PlanQty = qty;
                                            res.ShippingDate = shipping;
                                            res.SMKTDate = kitDate;
                                            res.WHSDate = kitDate;
                                            res.ShiftId = 1;
                                            res.OperationTime = item.FirstOrDefault(i => i.Product == res.Item);
                                            res.PlanedTime = res.PlanQty * res.OperationTime.SetTime;
                                            res.Breaks = res.Resource.BreakGroup;
                                            _production.Results.Add(res);
                                            
                                        }
                                    }
                                    int qty2;
                                    bool plan2 = Int32.TryParse(dt.Rows[i][col+6].ToString(),out qty2);
                                    
                                    if(plan2 && qty2 != 0){ //Turno 1
                                        Result res = new Result();
                                        res.Priority = 1;
                                        res.Date = date;
                                        res.Resource = resources.FirstOrDefault(r => r.Code == dt.Rows[i][0].ToString());
                                        
                                        if(res.Resource != null ){
                                            if(res.Resource.BreakGroupId != 0){
                                                res.Resource.BreakGroup = breaks.FirstOrDefault(b => b.Id == res.Resource.BreakGroupId);
                                            }
                                            //Turno Segun Columna
                                            res.Operators = op;
                                            res.Item = dt.Rows[i][3].ToString();
                                            res.WorkOrder = dt.Rows[i][5].ToString();
                                            res.OrderQty = orderQty;
                                            res.PlanQty = qty2;
                                            res.ShippingDate = shipping;
                                            res.SMKTDate = kitDate;
                                            res.WHSDate = kitDate;
                                            res.ShiftId = 2;
                                            res.OperationTime = item.FirstOrDefault(i => i.Product == res.Item);
                                            res.PlanedTime = res.PlanQty * res.OperationTime.SetTime;
                                            res.Breaks = res.Resource.BreakGroup;
                                            _production.Results.Add(res);
                                        }
                                    }
                                    date = date.AddDays(1);   

                                }
                                
                            }else{
                                
                            }
                        /*
                        }

                        /* ----- Planeacion de Produccion ------ */
                    }
                    return Ok(_production.SaveChanges());
                }
            }
            return BadRequest();
        }
        
    }
}