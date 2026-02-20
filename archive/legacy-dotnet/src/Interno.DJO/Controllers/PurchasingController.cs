using System;
using System.Linq;
using Microsoft.AspNetCore.Mvc;

using System.Data;
using System.Collections.Generic;
using Microsoft.AspNetCore.Http;
using Microsoft.EntityFrameworkCore;


using System.ComponentModel.DataAnnotations;
using System.IO;
using System.Globalization;
using CsvHelper;

namespace Interno.DJO.Controllers
{
    [Route("[controller]")]
    [ApiController]
    public class PurchasingController : ControllerBase
    {
        private readonly DJOContext _context;
        public PurchasingController(DJOContext context)
        {
            _context = context;
        }
        
        [HttpGet("LogTypes")]
        public IActionResult getLogtypes(){
            return Ok(_context.DJOLogTypes.ToList());
        }

        [HttpGet("Receipts")]
        public IActionResult getLastReceipts()
        {
            return Ok(_context.PurchaseReceipts.Max(e => e.ReceivedDate));
        }
        
        [HttpPost("PO")]
        [RequestFormLimits(MultipartBodyLengthLimit = 209715200)]
        [RequestSizeLimit(209715200)]
        public IActionResult setOpenPOs([FromForm] IFormFile file)
        {
            //Si contiene archivos 
            if(file.Length > 0){

                // List<Interno.DJO.Models.PurchaseOrder> list = _context.PurchaseOrders.ToList();
                
                DataTable Report = ReportController.ExcelToDataTable( file.OpenReadStream())[0];
                if(Report.Rows.Count > 0){ int count =  _context.Database.ExecuteSqlRaw("TRUNCATE TABLE `dbinterno`.`purchaseorders`;");} 
                foreach (DataRow row in Report.Rows)
                {//Search order registry
                    Interno.DJO.Models.PurchaseOrder order = //list.FirstOrDefault(p => 
                    //     p.PO.ToString() == row["pO#"].ToString()
                    //     && p.Line.ToString() == row["line"].ToString()
                    //     && p.Rel.ToString() == row["rel"].ToString()
                    //     && p.Ship.ToString() == row["ship"].ToString()
                    // ) ??
                     new Models.PurchaseOrder();

                    order.ShipTo = row["ship To"].ToString();
                    order.PO = Int32.Parse(row["po#"].ToString());
                    try{ order.Rel = Int32.Parse(row["rel"].ToString());
                    }catch(System.FormatException){}
                    order.Line = Int32.Parse(row["line"].ToString());
                    order.Ship = Int32.Parse(row["ship"].ToString());
                    order.Item = row["item"].ToString();
                    order.SupItem = row["sup Item"].ToString();
                    order.Supplier = row["supplier"].ToString();
                    order.QtyOrd =(row["qty Ord"].ToString()!="")? Decimal.Parse(row["qty Ord"].ToString()):0;
                    order.QtyRec = Decimal.Parse(row["qty Rec"].ToString());
                    order.QtyBilled = Decimal.Parse(row["qty Billed"].ToString());
                    try{ order.QtyDue = Decimal.Parse(row["qty due"].ToString());;
                    }catch(System.FormatException){}
                    order.QtyCancelled = Decimal.Parse(row["qty Cancelled"].ToString());
                    try{ DateTime.Parse(row["promised"].ToString());
                    }catch(System.FormatException){}
                    try{ order.NeedBy = DateTime.Parse(row["need By"].ToString()); }
                    catch(System.FormatException){}
                    order.OrderDate = DateTime.Parse(row["order Date"].ToString());
                    order.Buyer = row["buyer"].ToString();
                    order.Status = row["status"].ToString();
                    order.AuthorizationStatus = row["authorization Status"].ToString();
                    order.Price = Decimal.Parse( row["price"].ToString());
                    order.ShpAmount = Decimal.Parse( row["shp Amount"].ToString());
                    order.UOM = row["uom"].ToString();
                    order.Site = row["site"].ToString();
                    order.Curr = row["curr"].ToString();
                    order.CountryOfOrigen = row["country of Origin"].ToString();
                    order.ReceiptRouting = row["receipt Routing"].ToString();
                    _context.Add(order);
                }
                return Ok(_context.SaveChanges());
            }
            return BadRequest();
        }
        

        
        [HttpGet("PO/{filter}")]
        public IActionResult GetResource(string filter)
        {
            return Ok(_context.PurchaseOrders.Where(o => o.PO.ToString().Contains(filter) || o.Item.Contains(filter) || o.SupItem.Contains(filter) ).ToList());
        }

        [HttpGet("Incoming/Priorities")]
        public IActionResult getPendingPriorities()
        {
            var types = _context.DJOLogTypes.ToList();
            var list = _context.IncomingPriorities.Where(p => p.Available == false).ToList();
            foreach (var item in list)
            {
                item.Log = _context.DJOLog.Where(p => p.IncomingPriorityId == item.Id).OrderBy(p => p.Type.Id).ToList();

                foreach (var log in item.Log){ log.Type = types.FirstOrDefault(p => p.Id == log.Type.Id); }
                
                if(!item.Log.Any(l => l.Type.Id == 1)){
                    Interno.DJO.Models.DJOLog log1 = new Models.DJOLog();
                    log1.Type = types.FirstOrDefault(p => p.Id == 1);
                    log1.IncomingPriorityId = item.Id;
                    item.Log.Add(log1);
                }
                if(item.Log.Any(l => l.Type.Id == 1 && l.Date != DateTime.MinValue)){
                    if(!item.Log.Any(l => l.Type.Id == 2)){
                        Interno.DJO.Models.DJOLog log2 = new Models.DJOLog();
                        log2.Type = types.FirstOrDefault(p => p.Id == 2);
                        log2.IncomingPriorityId = item.Id;
                        item.Log.Add(log2);
                    }
                }
                if(item.Log.Any(l => l.Type.Id == 2 && l.Date != DateTime.MinValue)){
                    if(!item.Log.Any(l => l.Type.Id == 3)){
                        Interno.DJO.Models.DJOLog log3 = new Models.DJOLog();
                        log3.Type = types.FirstOrDefault(p => p.Id == 3);
                        log3.IncomingPriorityId = item.Id;
                        item.Log.Add(log3);
                    }
                    if(item.Log.Any(l => l.Type.Id == 3 && l.Date != DateTime.MinValue)){
                        if(!item.Log.Any(l => l.Type.Id == 4)){
                            Interno.DJO.Models.DJOLog log4 = new Models.DJOLog();
                            log4.Type = types.FirstOrDefault(p => p.Id == 4);
                            log4.IncomingPriorityId = item.Id;
                            item.Log.Add(log4);
                        }
                    }
                }
            }
            return Ok(list);
        }

        [HttpPost("Incoming/Priority")]
        public IActionResult setIncomingPriority(Interno.DJO.Models.IFormPriorityLog data)
        {
            if(data.ETA == DateTime.MinValue) ModelState.AddModelError("ETA","ETA Date is required.");
            if(data.Priority == 0) ModelState.AddModelError("Priority","Priority Level is required");
            if(ModelState.IsValid)
            {
                Interno.DJO.Models.IncomingPriority priority = new Interno.DJO.Models.IncomingPriority(data);
                priority.CreatedUser = HttpContext.User.Identity.Name.Split("\\")[1];
                priority.UpdatedUser = HttpContext.User.Identity.Name.Split("\\")[1];
                _context.IncomingPriorities.Add(priority);
                return Ok(_context.SaveChanges());
            }
            return BadRequest(ModelState);
        }

        
        [HttpGet("ScoreCard/Supplier/{supplier}")]
        public IActionResult getReceipts(string supplier)
        {
            var year = DateTime.Now.Year;
            //All receipts from Last Year 2022 -> 2021-01-01
            List<Interno.DJO.Models.PurchaseReceipts> receipts =_context.PurchaseReceipts.Where(p => p.FiscalYear >= year-1 && p.SupplierName == supplier).ToList();
            
            //Group Products in Receipts
            List<string> products = receipts.GroupBy(r => r.Product).Select(r => r.Key).ToList();
            //Get Prices List from Producs
            List<Interno.DJO.Models.ItemPrice> prices = _context.ItemPrices.Where(r => products.Contains(r.Item)).ToList();
            //Asign Std Cost to Products
            foreach (var item in receipts)
            {
                if(item.StdCost == 0){ 
                    var price = prices.FirstOrDefault(p => p.Item == item.Product);
                    if(price != null)   item.StdCost = decimal.Parse( price.StdCost.ToString());
                }
            }
            //Groyp Info by ProductNumber
            var ReceiptsLastYear = receipts.Where(r => r.ReceivedDate.Year == year-1).GroupBy(r => r.Product).Select(r => new IReceipts{
                Product = r.First().Product , StdCost = r.Sum(sm => sm.ReceiptAmount)/r.Sum(sm => sm.ReceivedQty),From = r.Min(rm =>rm.ReceivedDate), To = r.Max(rm =>rm.ReceivedDate)}).ToList();
            //Group info by FiscalYear, ProductNumber
            var ReceiptsActualYear = receipts.Where(r => r.FiscalYear == year).OrderBy(sr => sr.FiscalPeriod).ToList();
            var groupPeriod = ReceiptsActualYear.GroupBy(r => r.FiscalPeriod).Select( sr => new { 
                Supplier = supplier,
                FiscalPeriod = sr.Key,
                Receipts = sr.GroupBy(rg => rg.Product).Select(sr2 => new IReceipts{
                    Supplier = supplier,
                    Period = sr.Key,
                    Product = sr2.Key,
                    ReceivedAmount = sr2.Sum(sp => sp.ReceiptAmount),
                    ReceivedQty = sr2.Sum(sp => sp.ReceivedQty),
                    StdCost = Decimal.Round( sr2.Sum(sm => sm.ReceiptAmount)/sr2.Sum(sm => sm.ReceivedQty),6),
                    LastStdCost = Decimal.Round( ReceiptsLastYear.FirstOrDefault(lp => lp.Product == sr2.Key).StdCost ,6),
                    Inflation = Decimal.Round( (sr2.Sum(sm => sm.ReceiptAmount)/sr2.Sum(sm => sm.ReceivedQty) - decimal.Round( ReceiptsLastYear.FirstOrDefault(lp => lp.Product == sr2.Key).StdCost ,6)) * sr2.Sum(sp => sp.ReceivedQty) ,6),
                    // PPV = Decimal.Round( sr2.Average(sm => sm.PPV),6),
                    // Spend = Decimal.Round( sr2.Sum(sp => sp.ReceiptAmount)- sr2.Average(sm => sm.PPV) ,6),
                    
                }).ToList(),
            });
            
            List<IReceipts> list = new List<IReceipts>();
            foreach (var item in groupPeriod)
            {
                IReceipts per = new IReceipts();
                per.Supplier = item.Supplier;
                per.Period = item.FiscalPeriod;
                per.ReceivedAmount = item.Receipts.Sum(r => r.ReceivedAmount);
                per.ReceivedQty = item.Receipts.Sum(r => r.ReceivedQty);
                per.StdCost = item.Receipts.Sum(r => r.StdCost);
                per.LastStdCost = item.Receipts.Sum(r => r.LastStdCost);
                per.PPV = item.Receipts.Average(r => r.PPV);
                per.Inflation = item.Receipts.Sum(r => r.Inflation);
                per.Spend = item.Receipts.Sum(r => r.Spend);
                per.CostSaving = item.Receipts.Sum(r => r.Inflation) / item.Receipts.Sum(r => r.Spend);
                list.Add(per);
            }
          
            return Ok(list);
        }
        

        private class IReceipts
        {
            public string Supplier { get; set; }
            public string Period { get; set; }
            public string Product { get; set; }
            public decimal ReceivedAmount { get; set; }
            public decimal ReceivedQty { get; set; }
            public decimal StdCost { get; set; }
            public decimal LastStdCost { get; set; }
            public decimal Inflation { get; set; }
            public decimal PPV { get; set; }
            public decimal Spend { get; set;}
            public decimal CostSaving { get; set;}
            public DateTime? From { get; set; }
            public DateTime? To { get; set; }
        }
        public class IReceiptsSumarize
        {
            public string Supplier { get; set; }
            public string FiscalPeriod { get; set; }
            public decimal Inflation { get; set; }
            public decimal PPV { get; set; }
            public decimal Spend { get; set; }
            public decimal CostSaving { get; set; }
        }
    }
}