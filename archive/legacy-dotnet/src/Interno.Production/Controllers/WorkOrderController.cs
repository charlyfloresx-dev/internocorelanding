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

using Interno.Domain.Enum;


namespace Interno.Production.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class WorkOrderController : ControllerBase
    {
        private readonly ProductionContext _context;

        public WorkOrderController(ProductionContext context)
        {
            _context = context;
        }





        [HttpGet("Types")]
        public IActionResult GetOrderTypes() {
            return Ok(Enum.GetNames(typeof(WOType)));
        }
        
        [HttpPost("Upload")]
        public IActionResult uploadWorkOrders([FromForm] IFormFile file)
        {
            List<WorkOrder> errors = new List<WorkOrder>();
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
                    
                    var item = _context.OperationTime.ToList();
                    
                    DataTable dt = result.Tables[0];
                    
                    foreach (DataRow row in dt.Rows)
                    {
                        WorkOrder wo = new WorkOrder();
                        wo.Id = row[0].ToString();
                        wo.Type = (row[1].ToString().Split(" ")[0] == "Non-standard")? WOType.NonStandard : WOType.Standard;
                        wo.FinishItemCode = row[2].ToString();
                        wo.OrderQty = Int32.Parse( row[5].ToString());
                        wo.Status = StatusType.Released;
                        wo.Start = DateTime.Parse(row[7].ToString());
                        wo.Request = DateTime.Parse(row[8].ToString());
                        wo.Comment = row[9].ToString();
                        wo.Review ="N/A";
                        wo.OperationTime = item.FirstOrDefault(i => i.Product == wo.FinishItemCode);
                        if(wo.OperationTime != null){ wo.EstimatedTime = wo.OrderQty * wo.OperationTime.SetTime;
                        }else{ wo.Comment = wo.Comment+" | NO STANDARD TIME "; }
                        if(!_context.WorkOrders.Any(w => w.Id == wo.Id)){
                            _context.WorkOrders.Add(wo);
                        }else{
                            _context.WorkOrders.Update(wo);
                            wo.Comment = wo.Comment+" | Exist ";
                            errors.Add(wo);
                        }   
                    }
                }
            }
            return Ok(new{Add = _context.SaveChanges(),Errors = errors});
        }
 

        // POST: api/WorkOrder
        // To protect from overposting attacks, enable the specific properties you want to bind to, for
        // more details, see https://go.microsoft.com/fwlink/?linkid=2123754.
        [HttpPost]
        public IActionResult PostWorkOrder(WorkOrder workOrder)
        {
            if(workOrder.OrderQty == 0) ModelState.AddModelError("OrderQty","Order Qty is required.");
            if(workOrder.Request == DateTime.MinValue) ModelState.AddModelError("Request","Request Date is required.");

            if(ModelState.IsValid){
                if(workOrder.Guid == Guid.Empty){ workOrder.Guid = Guid.NewGuid();}
                if(workOrder.CustomerId == 0) workOrder.CustomerId = 1;
                /*workOrder.FinishItem = _context.Item.FirstOrDefault(i => i.Code == workOrder.FinishItemCode);
                
                if(workOrder.FinishItem != null) 
                {
                    workOrder.FinishItem.Category = null;
                    workOrder.Alias = (workOrder.FinishItem.Name != "")? workOrder.FinishItem.Name : workOrder.FinishItem.Alias;
                }
                */
                
                _context.WorkOrders.Add(workOrder);
                _context.SaveChanges();
                return CreatedAtAction("GetWorkOrder", new { id = workOrder.Id }, workOrder);
            }
            return BadRequest(ModelState);
        }



        private bool WorkOrderExists(string id)
        {
            return _context.WorkOrders.Any(e => e.Id == id);
        }
    }
}
