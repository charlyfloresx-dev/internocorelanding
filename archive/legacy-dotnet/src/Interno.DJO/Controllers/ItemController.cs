
using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.AspNetCore.Mvc;

using System.Data;
using Microsoft.AspNetCore.Http;
using Microsoft.EntityFrameworkCore;

namespace Interno.DJO.Controllers
{
    [ApiController]
    [Route("[controller]")]
    public class ItemController : ControllerBase
    {
        private readonly DJOContext _context;
        private readonly Interno.Production.Models.ProductionContext _production;

        public ItemController(DJOContext context, Interno.Production.Models.ProductionContext production)
        {
            _context = context;
            _production = production;
        }
        [HttpGet]
        public IActionResult getItems() => Ok(_context.ItemPrices.FirstOrDefault());

        [HttpPost]
        [RequestFormLimits(MultipartBodyLengthLimit = 209715200)]
        [RequestSizeLimit(209715200)]
        public IActionResult setItems([FromForm] IFormFile file)
        {//Si contiene archivos 
            if (file.Length > 0)
            {
                List<Interno.DJO.Models.ItemPrice> list = _context.ItemPrices.ToList();
                DataTable Report = ReportController.ExcelToDataTable(file.OpenReadStream())[0];
                Object[] last = Report.Rows[Report.Rows.Count - 1].ItemArray;
                List<Interno.DJO.Models.ItemPrice> errors = new List<Interno.DJO.Models.ItemPrice>();
                int updated = 0;
                int con = 0;
                foreach (DataRow row in Report.Rows)
                {
                    Interno.DJO.Models.ItemPrice item = list.FirstOrDefault(p => p.Item == row["item"].ToString() && p.Site == row["site"].ToString()) ?? new Models.ItemPrice();
                    item.Item = row["item"].ToString();
                    item.Description = row["description"].ToString();
                    item.UOM = row["unit Of Measure"].ToString();
                    item.Site = row["site"].ToString();
                    item.Status = row["item Status"].ToString();
                    item.Type = row["item Type"].ToString();
                    item.CorporateBrand = row["corporate Brand"].ToString();
                    //item.ABC = (row["abc"].ToString().Length > 1)? Char.Parse(row["abc"].ToString().Substring(0,1)) : Char.MinValue;
                    item.StdCost = Double.Parse(row["std Cost"].ToString());
                    item.Buyer = row["buyer"].ToString();
                    item.Supplier = row["supplier"].ToString();
                    item.MOQ = Decimal.Parse(row["moq"].ToString());
                    item.MPQ = Decimal.Parse(row["mpq"].ToString());
                    item.LeadTime = Decimal.Parse(row["lead Time"].ToString());
                    item.PriorityCode = Int16.Parse(row["priority Code"].ToString());
                    item.SafetyStock = Decimal.Parse(row["safety Stock"].ToString());
                    _context.AddOrUpdate(item);
                    con++;
                    try
                    {
                        if ((con % 1000) == 0) { updated += _context.SaveChanges(); Console.WriteLine(con); }
                    }
                    catch (Microsoft.EntityFrameworkCore.DbUpdateConcurrencyException) { }
                }
                updated += _context.SaveChanges();
                return Ok(new { updated, errors });

            }
            return BadRequest("Error");
        }



        [HttpPost("Upload/OperationTimes")]
        [RequestFormLimits(MultipartBodyLengthLimit = 209715200)]
        [RequestSizeLimit(209715200)]
        public IActionResult uploadOperationTimes([FromForm] IFormFile file)
        {//Si contiene archivos 
            if (file.Length > 0)
            {
                List<string> whs = _production.Resource.Select(r => r.Code).ToList();
                DataTable Report = ReportController.ExcelToDataTable(file.OpenReadStream())[0];
                List<Production.Models.OperationTime> times = _production.OperationTime.ToList();
                try
                {
                    for (int i = 2; i < Report.Rows.Count; i++)
                    {
                        //if(whs.Any(w => w == Report.Rows[i][6].ToString())){
                        var temp = Report.Rows[i][0].ToString();
                        Interno.Production.Models.OperationTime time = times.FirstOrDefault(i => i.Product == temp) ?? new Production.Models.OperationTime();
                        time.Product = Report.Rows[i][0].ToString();
                        time.Description = Report.Rows[i][1].ToString();
                        time.Operation = Report.Rows[i][2].ToString();
                        time.WarehouseCode = (whs.Any(w => w == Report.Rows[i][6].ToString())) ? Report.Rows[i][6].ToString() : "NOCELL";
                        time.Hours = Double.Parse(Report.Rows[i][5].ToString());
                        time.RunTime = TimeSpan.FromHours(time.Hours);
                        //time.Username = HttpContext.User.Identity.Name.Split("\\")[1];
                        _production.AddOrUpdate(time);
                        //}
                    }
                    return Ok(_production.SaveChanges());
                }
                catch (Microsoft.EntityFrameworkCore.DbUpdateConcurrencyException) { }
            }
            return BadRequest();
        }
    }
}
