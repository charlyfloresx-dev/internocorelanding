using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Interno.Inventory.Models;
using Interno.Production.Models;
using System.Globalization;
using System.Data;
using ExcelDataReader;
using CsvHelper;

namespace Interno.Production.Controllers
{
    
    [Route("api/[controller]")]
    [ApiController]
    public class ItemController : ControllerBase
    {
        private readonly ProductionContext _context;
        CultureInfo provider = CultureInfo.InvariantCulture;

        public ItemController(ProductionContext context)
        {
            _context = context;
        }

        // GET: api/Item
        [HttpGet]
        public async Task<ActionResult<IEnumerable<Item>>> GetItem()
        {
            return await _context.Item.Include(i => i.Category).ToListAsync();
        }

        // GET: api/Item/5
        [HttpGet("{id}")]
        public IActionResult GetItem(string id)
        {
            var item = _context.Item.Include(i => i.Category).FirstOrDefault(i => i.Code == id);

            if (item == null)
            {
                return NotFound();
            }

            return Ok(item);
        }

      

        [HttpPost("Times/Update")]
        public IActionResult setTimesUpdate([FromForm] IFormFile file)
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
                    var item = _context.OperationTime.ToList();
                    
                    DataTable dt = result.Tables[0];
                    foreach (DataRow row in dt.Rows)
                    {
                        OperationTime op = new OperationTime();
                        if(row[5].ToString() != "" || row[4].ToString() != ""){
                            op.Guid = Guid.NewGuid();
                                op.Product = row[0].ToString();
                                op.Operators =Int16.Parse( row[2].ToString());
                                op.Description = row[3].ToString();
                                op.Operation = "Final";
                                Console.WriteLine(row[4].ToString());
                                op.RunTime = TimeSpan.FromSeconds(Decimal.ToDouble(Math.Ceiling( Decimal.Parse(row[4].ToString()))));
                                op.SetTime = (row[5].ToString() != "")? TimeSpan.FromSeconds(Decimal.ToDouble(Math.Ceiling( Decimal.Parse(row[5].ToString())))) : (op.RunTime * 0.85);
                            if(!item.Any(i => i.Product == row[0].ToString())){
                                _context.OperationTime.Add(op);
                            }else { _context.OperationTime.Update(op);}
                            
                        }
                    }
                    return Ok(_context.SaveChanges());
                }
            }
            return BadRequest();
        }


        private bool ItemExists(Guid id)
        {
            return _context.Item.Any(e => e.Guid == id);
        }
    }
}