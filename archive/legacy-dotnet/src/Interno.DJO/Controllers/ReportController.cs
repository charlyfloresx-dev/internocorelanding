using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Interno.DJO.Models;
using Interno.DJO.Helpers;

using System.IO;
using System.Globalization;
using System.Data;
using System.Text.RegularExpressions;

using CsvHelper;
using ExcelDataReader;

namespace Interno.DJO.Controllers
{
    [ApiController]
    [Route("[controller]")]
    public class ReportController : ControllerBase
    {
        public CultureInfo provider = CultureInfo.InvariantCulture;
        //Database Context
        private readonly DJOContext _context;
        private readonly Interno.Production.Models.ProductionContext _production;
        public ReportController(DJOContext context, Interno.Production.Models.ProductionContext production)
        {    
            _context = context;
            _production = production; 
        }
       
        [HttpPost("BOM")]
        [RequestFormLimits(MultipartBodyLengthLimit = 209715200)]
        [RequestSizeLimit(209715200)]
        public IActionResult updateBOM([FromForm] IFormFile file)
        {
            //List<BOM> listBom = _context.BOMs.ToList();
            //Si contiene archivos 
            if(file.Length > 0){
                DataTable Report = ReportController.ExcelToDataTable( file.OpenReadStream())[0];
                
                if(Report.Rows.Count > 0){ int count =  _context.Database.ExecuteSqlRaw("TRUNCATE TABLE `dbinterno`.`boms`;");} 
                int updated = 0;
                for (int i = 1; i < Report.Rows.Count; i++)
                {
                    List<object[]> error = new List<object[]>();
                    BOM item = new BOM();    
                        var itemPart = Report.Rows[i][0].ToString();
                        // var tempbom = listBom.Where(b => b.Item == itemPart).ToList();
                        // foreach (var tb in tempbom){ _context.BOMs.Remove(tb); _context.SaveChanges();}
                        
                        item.Item = itemPart;
                        item.Description = Report.Rows[i][1].ToString();
                        item.TypeDescription = Report.Rows[i][2].ToString();
                        item.Type = Report.Rows[i][3].ToString();
                        item.Module = Report.Rows[i][4].ToString();
                        item.Status = Report.Rows[i][5].ToString();
                        item.Level = Int16.Parse(Report.Rows[i][6].ToString() ); 
                        item.Parent = Report.Rows[i][7].ToString();
                        item.Component = Report.Rows[i][8].ToString();
                        item.ComponentDescription = Report.Rows[i][9].ToString();
                        try{
                            item.ComponenQuantityPer = Decimal.Parse( Report.Rows[i][10].ToString(),System.Globalization.NumberStyles.Any);
                        }catch(System.FormatException){ return Ok(Report.Rows[i][10].ToString()); }
                        
                        item.UOM = Report.Rows[i][11].ToString();
                        item.ComponentType = Report.Rows[i][12].ToString();
                        item.ComponentModule = Report.Rows[i][13].ToString();
                        item.ComponentSupplierType = Report.Rows[i][14].ToString();
                        item.Id = i;
                        _context.AddOrUpdate(item);

                        if((i % 1000) == 0){
                            updated += _context.SaveChanges();
                            Console.WriteLine(updated);
                        }
                        Console.WriteLine(i);
                }
                return Ok(updated += _context.SaveChanges());
            }
            return BadRequest();
        }

        [HttpPost("OTD")]
        [RequestFormLimits(MultipartBodyLengthLimit = 209715200)]
        [RequestSizeLimit(209715200)]
        public IActionResult setOTDData([FromForm] IFormFile file)
        {
            if(file.Length > 0){
                int updated = 0;
                DataTable temp = ReportController.CSVtoDataTable(file.OpenReadStream());
                //_context.Database.ExecuteSqlRaw("TRUNCATE TABLE `dbinterno`.`otdreceipts`;");
                for (int i = 0; i < temp.Rows.Count; i++)
                {
                    OTDReceipt otd = new OTDReceipt();
                    
                    otd.OrganizationCode = temp.Rows[i]["organization Code"].ToString();
                    otd.Type = temp.Rows[i]["item Type"].ToString();
                    otd.Item = temp.Rows[i]["item$Item"].ToString();
                    otd.Vendor = temp.Rows[i]["vendor Name"].ToString();
                    otd.PO = Int32.Parse (temp.Rows[i]["po Document Number"].ToString());
                    otd.Line = Int16.Parse( temp.Rows[i]["po Document Line Number"].ToString());
                    try{    otd.Release = Int16.Parse( temp.Rows[i]["release Number"].ToString() );
                    }catch(System.FormatException){}
                    otd.POshipmentNumber = Int16.Parse(temp.Rows[i]["po Shipment Number"].ToString());
                    otd.ReceiptCreationDate = DateTime.Parse( temp.Rows[i]["receipt Creation Date"].ToString());
                    otd.QuantityReceived = Decimal.Parse( temp.Rows[i]["quantity Received"].ToString());
                    otd.Buyer = temp.Rows[i]["buyer Name"].ToString();
                    otd.PrimaryQuantity = Decimal.Parse( temp.Rows[i]["primary Quantity"].ToString());
                    otd.PromisedDate = (temp.Rows[i]["promised Date"].ToString() != "")? DateTime.Parse( temp.Rows[i]["promised Date"].ToString()) : DateTime.MinValue;
                    otd.TransactionType = temp.Rows[i]["transaction Type"].ToString();
                    otd.TransactionType2 = temp.Rows[i]["transaction Type1"].ToString();
                    otd.OnTime = (otd.PromisedDate != DateTime.MinValue )? otd.PromisedDate > otd.ReceiptCreationDate : true ;
                    _context.AddOrUpdate(otd);
                    if((i % 1000) == 0){ updated += _context.SaveChanges(); }
                }
                return Ok(updated += _context.SaveChanges());
            }
            return BadRequest();
        }

        [HttpPost("SupplyDemand")]
        [RequestFormLimits(MultipartBodyLengthLimit = 209715200)]
        [RequestSizeLimit(209715200)]
        public IActionResult setSuppliDemand([FromForm] IFormFile file)
        {
            if(file.Length > 0){
                
                DataTable Report = ReportController.ExcelToDataTable( file.OpenReadStream())[0];
                
                var updated = 0;
                if(Report.Rows.Count > 0){
                    var count =  _context.Database.ExecuteSqlRaw("set foreign_key_checks=0; TRUNCATE TABLE `dbinterno`.`supplydemands`;");
                    count =  _context.Database.ExecuteSqlRaw("set foreign_key_checks=0; TRUNCATE TABLE `dbinterno`.`projecteddates`;");
                } 
                for (int i = 3; i < Report.Rows.Count; i = i+3)
                {
                    
                    if(Report.Rows[i][0].ToString().Length > 0){
                        SupplyDemand sup = new SupplyDemand();
                        sup.Item = Report.Rows[i][0].ToString();
                        sup.Description = Report.Rows[i][5].ToString();
                        sup.Type =Report.Rows[i][2].ToString();
                        sup.Site = Report.Rows[i][1].ToString();
                        sup.Cell = Report.Rows[i][8].ToString();
                        sup.Buyer = Report.Rows[i][9].ToString();
                        sup.Supplier = Report.Rows[i][10].ToString();
                        sup.ABC = Report.Rows[i][3].ToString();
                    
                        try{
                            sup.LeadTime = Decimal.Parse(Report.Rows[i][11].ToString());
                        }catch(System.FormatException){}
                        
                        sup.LTDate = (Report.Rows[i][12].ToString() == "")? DateTime.MinValue : DateTime.Parse(Report.Rows[i][12].ToString());
                        if(Report.Rows[i][13].ToString()!= "Future"){
                            sup.ShortageDate = (Report.Rows[i][13].ToString() == "")? DateTime.MinValue : DateTime.Parse(Report.Rows[i][13].ToString());
                        }
                        
                        
                        //try{
                            sup.StdUnitCost = Decimal.Parse(Report.Rows[i][15].ToString().Replace("$",""),System.Globalization.NumberStyles.Any);
                        //}catch(System.FormatException){return BadRequest(Report.Rows[i][10].ToString());}
                        
                        sup.SafetyStockQty = Decimal.Parse(Report.Rows[i][16].ToString());
                        
                        try{
                        sup.OnHand = Decimal.Parse(Report.Rows[i][15].ToString(),System.Globalization.NumberStyles.Any);
                        }catch(System.FormatException){ }
                        sup.OpenPOs = Decimal.Parse(Report.Rows[i][16].ToString());
                        sup.ProjectedDates = new List<ProjectedDate>();
                        
                        List<ProjectedDate> projected = new List<ProjectedDate>();
                        
                        //Weeks
                            for (int c = 21; c < 31; c++)
                            {
                                var date = DateTime.MinValue;
                                DateTime.TryParse(Report.Rows[1][c].ToString(), out date);
                               
                                ProjectedDate temp2 = new ProjectedDate();
                                temp2.Date = date;
                                temp2.Type = "Balance";
                                try{
                                    temp2.Qty = Decimal.Parse( Report.Rows[i+1][c].ToString(),System.Globalization.NumberStyles.Any);
                                }catch(System.FormatException){ return BadRequest(Report.Rows[i+1][c].ToString());}
                                
                                sup.ProjectedDates.Add(temp2); 
                            }
                        
                        _context.SupplyDemands.Add(sup);
                        
                    }
                }
                //if(Report.Rows.Count > 0){ int count =  _context.Database.ExecuteSqlRaw("TRUNCATE TABLE `dbinterno`.`opensummaryreports`;");} 
                return Ok(updated += _context.SaveChanges());
            }
            return BadRequest();
        }
        
        [HttpPost("STBL")]
        [RequestFormLimits(MultipartBodyLengthLimit = 209715200)]
        [RequestSizeLimit(209715200)]
         public IActionResult setSTBLReport([FromForm] IFormFile file)
        {
            //Si contiene archivos 
            if(file.Length > 0){
                DataTable Report = ReportController.ExcelToDataTable( file.OpenReadStream())[0];
                int count =  _context.Database.ExecuteSqlRaw("TRUNCATE TABLE `dbinterno`.`stblonhandbuildreports`;");
                //var tempReport = Report.AsEnumerable().Where(r => r.Field<string>("column25") == "No Inventory to Build" ).ToList();
                
                for (int i = 2; i < Report.Rows.Count; i++)
                {
                    STBLOnHandBuildReport rep = new STBLOnHandBuildReport();
                    rep.PartName = Report.Rows[i][0].ToString();
                    rep.Description = Report.Rows[i][1].ToString();
                    rep.Site = Report.Rows[i][2].ToString();
                    rep.Type = Report.Rows[i][3].ToString();
                    rep.SourceType = Report.Rows[i][4].ToString();
                    rep.Source = Report.Rows[i][5].ToString();
                    rep.Buyer = Report.Rows[i][6].ToString();
                    rep.Cell = Report.Rows[i][7].ToString();
                    rep.OrderType = Report.Rows[i][8].ToString();
                    rep.Status = Report.Rows[i][9].ToString();
                    rep.DemandPlanSegment = Report.Rows[i][10].ToString();
                    rep.OrderLine = Report.Rows[i][11].ToString();
                    rep.CorporateBrand = Report.Rows[i][12].ToString();
                    try{ rep.RequestDate = DateTime.Parse( Report.Rows[i][13].ToString() );}catch(System.FormatException){  }
                    rep.ShortCompCount =(! String.IsNullOrEmpty(Report.Rows[i][14].ToString()))? Int16.Parse( Report.Rows[i][14].ToString() ) :0;
                    try{
                        rep.Hold = Char.Parse( Report.Rows[i][15].ToString() );
                    }catch(System.FormatException){ return Ok(new{Report.Rows[i].ItemArray,Row = Report.Rows[i][15].ToString()}); }
                    try{ rep.Quantity = Decimal.Parse(Report.Rows[i][16].ToString()); }catch(System.FormatException){  }
                    rep.UnitSellingPrice = Decimal.Parse( Report.Rows[i][17].ToString() );
                    rep.ExtValue = Decimal.Parse(Report.Rows[i][18].ToString());
                    try{ rep.FGOnHandQty = Decimal.Parse( Report.Rows[i][19].ToString());
                    }catch(System.FormatException){return BadRequest(new{rep,Report.Rows[i].ItemArray});}
                    rep.QtyOnWorngOrg = Int16.Parse( Report.Rows[i][20].ToString());
                    try{ rep.TotalBuildQuantity = Decimal.Parse( Report.Rows[i][22].ToString());
                    }catch(System.FormatException){return BadRequest(new{rep,Report.Rows[i].ItemArray});}
                    try{
                        rep.STBLQtyInpanct = Int32.Parse(Report.Rows[i][23].ToString());
                    }catch(System.FormatException){ }//return BadRequest(Math.Round( Decimal.Parse( Report.Rows[i][23].ToString()),0));}
                    
                    rep.NetOH = Decimal.Parse( Report.Rows[i][24].ToString());
                    rep.RoutCauses = Report.Rows[i][25].ToString();
                    rep.Notes = Report.Rows[i][26].ToString();
                    _context.STBLOnHandBuildReports.Add(rep);
                }
                var updated = new {
                    Updated = _context.SaveChanges(),
                    STBL = _context.STBLOnHandBuildReports.ToList().Where(s => s.RoutCauses == "No Inventory to Build" ).GroupBy(s => s.MfgPfg).Select(s => new{ s.Key, Sum = s.Sum(s => s.STBLQtyInpanct)})
                };
                    STBLTrend trend = new STBLTrend{
                        Date = InternoExtensions.FirstDayOfWeek(DateTime.Now.Date),//Primer dia de la Semana Actual de ANio
                        MFG = updated.STBL.FirstOrDefault(s => s.Key == "MFG").Sum *-1,
                        PFG = updated.STBL.FirstOrDefault(s => s.Key == "PFG").Sum *-1,
                        Target = 4500
                    };
                    //Si ya existe Registro de STBL de la Semana
                    if(!_context.STBLTrends.Any(s => s.Date.Date == trend.Date.Date)){ _context.STBLTrends.Add(trend); }
                    else{  _context.STBLTrends.Update(trend); }
                
                    //Format & Complete Report
                    List<STBLOnHandBuildReport> stbl = _context.STBLOnHandBuildReports.Where(r => r.RoutCauses == "No Inventory to Build" ).OrderBy(r => r.RequestDate).ToList();
                    //return Ok(stbl);
                    //Agrupamos Parent Items List
                    List<string> items = stbl.GroupBy(r => r.PartName).Select(r => r.Key).ToList();
                    //Explotamos el BOM de los Items en el Listado
                    List<BOM> boms = _context.BOMs.Where(b => items.Contains(b.Item)).OrderBy(b => b.Id).ToList();
                    
                    //Filtramos por Componentes
                    List<string> components = boms.GroupBy(b => b.Component).Select(c=> c.Key).ToList();
                    
                    //Revisamos el OpenSummary Report por Componente
                    List<OpenSummaryReport> summary = _context.OpenSummaryReports.Where(s => components.Contains(s.Part) || items.Contains(s.Part)).ToList();

                    List<SupplyDemand> supply =_context.SupplyDemands.Where(s => components.Contains(s.Item)).ToList();

                    //Caragamos Taxonomy
                    List<Taxonomy> _tax = _context.Taxonomies.Where(tx => components.Contains(tx.ProductNumber) || items.Contains(tx.ProductNumber)).ToList();
                   
                    int con = 0;
                    foreach (var item in stbl)
                    {
                        if(item.MfgPfg != "PFG"){//SI ES MFG
                            //Emplotamos el BOM y Cargamos la demanda de cada componente solo Raw Material,
                            // verificando si tienen OnHand = 0 y tomando la fecha mas proxima de Corto
                            item.SupplyDemand = boms.Where(b => b.Item == item.PartName && b.ComponentType == "Raw Material")
                                                    .Join(supply, bom => bom.Component , sup => sup.Item, (bom,sup) => sup)
                                                    .Where(sd => sd.OnHand == 0).OrderBy(sd => sd.ShortageDate).GroupBy(sd => sd.Item).Select(sd => sd.FirstOrDefault()).ToList();
                            
                            if(item.SupplyDemand.Count > 0){
                                foreach (var comp in item.SupplyDemand)
                                {   //SumaryReport del Componenete para agarrar fecha mas Proxima
                                    comp.OpenSummaryReport = summary.Where(s => s.Part == comp.Item).OrderBy(s => s.DueDate).FirstOrDefault();
                                    if(comp.OpenSummaryReport != null){
                                        item.ComponentDueDate = comp.OpenSummaryReport.DueDate ;
                                        item.Component = comp.OpenSummaryReport.Part;
                                        item.Supplier =  comp.OpenSummaryReport.SupplierDescription;
                                        item.Notes ="RM "+ item.Component+" "+item.ComponentDueDate.Date.ToString("MM/dd"); 
                                    } 
                                }
                            }
                        }else{//SI ES PFG
                            var OpenSummaryReport = summary.Where(s => s.Part == item.PartName).OrderBy(s => s.DueDate).FirstOrDefault();
                            if(OpenSummaryReport != null){
                                item.ComponentDueDate = OpenSummaryReport.DueDate ;
                                item.Component = OpenSummaryReport.Part;
                                item.Supplier =  OpenSummaryReport.SupplierDescription;
                                item.Notes = item.Component+" "+item.ComponentDueDate.Date.ToString("MM/dd"); 
                            }
                        }
                        var tx = _tax.FirstOrDefault(t => t.ProductNumber == item.PartName);
                        item.Category = (tx != null)? tx.PurchaseCategory : null;
                        var tb = boms.FirstOrDefault(b => b.Component == item.PartName);
                        item.Module = (tb != null)? tb.Module : null;
                        _context.STBLOnHandBuildReports.Update(item);
                        con ++;
                    }
                    // var Receipts = _context.PurchaseReceipts.Where(r => r.ReceivedDate.Month == DateTime.Now.Month && r.ReceivedDate.Year == DateTime.Now.Year);

                    // var temp = stbl.GroupBy(g => g.Supplier).Select(s => new{
                    //     Supplier = s.Key, 
                    //     MfgPfg = s.GroupBy(s => s.MfgPfg).Select(s => new{Type = s.Key, Sum = s.Sum(s => s.STBLQtyInpanct)}),
                    //     STBL = s.Sum(s => s.STBLQtyInpanct)*-1,
                    //     Receipts = Receipts.Where(r => r.SupplierName == s.Key).Sum(s => s.ReceivedQty),
                    //     DaysOfShortage = (Receipts.Where(r => r.SupplierName == s.Key).Sum(s => s.ReceivedQty) != 0 && s.Sum(s => s.STBLQtyInpanct) != 0)? 
                    //         (s.Sum(s => s.STBLQtyInpanct)*-1) *22 / Receipts.Where(r => r.SupplierName == s.Key).Sum(s => s.ReceivedQty)
                    //         : 0
                    // });

                    // List<ISTBL> supliersSTBL = new List<ISTBL>();

                    // foreach (var item in temp)
                    // {
                    //     supliersSTBL.Add( new ISTBL{
                    //         Supplier = item.Supplier,
                    //         STBL = item.STBL,
                    //         ReceiptsQty = item.Receipts,
                    //         DaysOfShortages = item.DaysOfShortage,
                    //         Score = (item.DaysOfShortage >= 0 && item.DaysOfShortage <4)? 15 - (Int16.Parse( Math.Round(item.DaysOfShortage).ToString())*5) : 0
                    //     });
                    // }
                    //Generamos el documento
                    // var stream = new MemoryStream();
                    // //Escribimos en el Documento
                    // using(var writeFile = new StreamWriter(stream, leaveOpen: true)) {
                    //     var csv = new CsvWriter(writeFile, provider);
                    //     //csv.Configuration.RegisterClassMap<GroupReportCSVMap>();            
                    //     csv.WriteRecords(supliersSTBL);
                    // }
                    // stream.Position = 0; //reset stream
                    // //Regresamos Documento CSV
                    // return File(stream, "application/octet-stream", "STBL"+DateTime.Now.Date.ToString()+".csv");
                    //return Ok(supliersSTBL);
                    return Ok(new{updated, trend,save = _context.SaveChanges()});
            }
            return BadRequest();
        }

        
        public class ISTBL{
            public string Supplier { get; set; }
            // public int PFG { get; set; }
            // public int MFG { get; set; }
            public int STBL { get; set; }
            public decimal ReceiptsQty { get; set; }
            public decimal DaysOfShortages { get; set; }
            public int Score { get; set; }
        }
        
        
        [HttpPost("SummaryReport")]
        [RequestFormLimits(MultipartBodyLengthLimit = 209715200)]
        [RequestSizeLimit(209715200)]
        public IActionResult setSummaryReport([FromForm] IFormFile file)
        {
            if(file.Length > 0){
                DataTable Report = ReportController.ExcelToDataTable( file.OpenReadStream())[0];
                if(Report.Rows.Count > 0){ int count =  _context.Database.ExecuteSqlRaw("TRUNCATE TABLE `dbinterno`.`opensummaryreports`;");} 
                for (int i = 1; i < Report.Rows.Count; i++)
                {
                    OpenSummaryReport rep = new OpenSummaryReport();
                    rep.Id = i;
                    rep.Site = Report.Rows[i][0].ToString();
                    rep.Part = Report.Rows[i][1].ToString();
                    rep.Description = Report.Rows[i][2].ToString();
                    rep.Buyer = Report.Rows[i][3].ToString();
                    rep.Organization = Report.Rows[i][4].ToString();
                    rep.Order = Report.Rows[i][5].ToString();
                    rep.Line = Report.Rows[i][6].ToString();
                    rep.OrderType = Report.Rows[i][7].ToString();
                    rep.Supplier = Report.Rows[i][8].ToString();
                    rep.SupplierDescription = Report.Rows[i][9].ToString();
                    rep.UOM = Report.Rows[i][10].ToString();
                    rep.Status = Report.Rows[i][11].ToString();
                    rep.OrgQuantity = Decimal.Parse( Report.Rows[i][12].ToString());
                    try{ rep.OpenQuantity = Decimal.Parse( Report.Rows[i][13].ToString());
                    }catch(System.FormatException){return BadRequest( Report.Rows[i].ItemArray);}
                    rep.ShipTo = Report.Rows[i][14].ToString();
                    var dat1 = DateTime.MinValue;
                    DateTime.TryParse(Report.Rows[i][15].ToString(),out dat1);
                    rep.DueDate = dat1;
                    var dat2 = DateTime.MinValue;
                    DateTime.TryParse(Report.Rows[i][15].ToString(), out dat2);
                    rep.OriginalDueDate = dat2;
                    rep.UnitPrice = Decimal.Parse( Report.Rows[i][17].ToString());
                    rep.Amount = Decimal.Parse( Report.Rows[i][18].ToString());
                    _context.OpenSummaryReports.Add(rep);
                }
                return Ok(_context.SaveChanges());
            }
            return BadRequest();
        }
        
        [HttpPost("Taxonomy")]
        [RequestFormLimits(MultipartBodyLengthLimit = 209715200)]
        [RequestSizeLimit(209715200)]
        public IActionResult updateTaxonomy([FromForm] IFormFile file)
        {
            //List<BOM> listBom = _context.BOMs.ToList();
            //Si contiene archivos 
            if(file.Length > 0){
                DataTable Report = ReportController.ExcelToDataTable( file.OpenReadStream())[0];
                try{
                    if(Report.Rows.Count > 0){ int count =  _context.Database.ExecuteSqlRaw("TRUNCATE TABLE `dbinterno`.`taxonomies`;");} 
                    int updated = 0;
                    for (int i = 1; i < Report.Rows.Count; i++)
                    {
                        Taxonomy tax = new Taxonomy();
                        tax.ProductNumber = Report.Rows[i][0].ToString();
                        tax.ProductName = Report.Rows[i][1].ToString();
                        tax.PurchaseClass = Report.Rows[i][2].ToString();
                        tax.PurchaseCategory = Report.Rows[i][3].ToString();
                            _context.Taxonomies.Add(tax);
                            if((i % 1000) == 0){
                                updated += _context.SaveChanges();
                            }
                            Console.WriteLine(i);
                    }
                    return Ok(updated += _context.SaveChanges());
                }catch(System.InvalidOperationException){}
            }
            return BadRequest();
        }

        [HttpPost("BuyerToolKit")]
        [RequestFormLimits(MultipartBodyLengthLimit = 209715200)]
        [RequestSizeLimit(209715200)]
        public IActionResult updateBuyerToolKit([FromForm] IFormFile file)
        {
            //List<BOM> listBom = _context.BOMs.ToList();
            //Si contiene archivos 
            if(file.Length > 0){
                DataTable Report = ReportController.ExcelToDataTable( file.OpenReadStream())[0];
                
                int updated = 0;
                for (int i = 2; i < Report.Rows.Count; i++)
                {
                    Interno.DJO.Models.BuyerKit bk = new BuyerKit();
                    bk.Item = Report.Rows[i][0].ToString();
                    bk.Site = Report.Rows[i][1].ToString();
                    bk.SRC = Report.Rows[i][2].ToString();
                    bk.Type = Report.Rows[i][3].ToString();
                    bk.Status = Report.Rows[i][5].ToString();
                    bk.ABC = Report.Rows[i][7].ToString();
                    bk.Buyer = Report.Rows[i][8].ToString();
                    bk.ItemDescription = Report.Rows[i][9].ToString();
                    bk.FirstShortage = (Report.Rows[i][10].ToString() !="")? DateTime.Parse( Report.Rows[i][10].ToString()) : DateTime.MinValue;
                    bk.DOS = Decimal.Parse( Report.Rows[i][11].ToString());
                    bk.SS = Decimal.Parse( Report.Rows[i][12].ToString());
                    bk.UOM = Report.Rows[i][13].ToString();
                    bk.LT = Decimal.Parse( Report.Rows[i][14].ToString());
                    bk.Min = Decimal.Parse( Report.Rows[i][15].ToString());
                    bk.Max = Decimal.Parse( Report.Rows[i][16].ToString());
                    bk.Multi = Decimal.Parse( Report.Rows[i][17].ToString());
                    bk.Supplier = Report.Rows[i][18].ToString();
                    bk.OH = Decimal.Parse( Report.Rows[i][19].ToString());
                    bk.PO = Decimal.Parse( Report.Rows[i][20].ToString());
                    bk.PLO = Decimal.Parse( Report.Rows[i][21].ToString());
                    bk.DMD = Decimal.Parse( Report.Rows[i][22].ToString());
                    bk.Date = InternoExtensions.FirstDayOfWeek( DateTime.Parse("2023-03-06"));
                    
                    _context.BuyerKits.Add(bk);
                    if((i % 1000) == 0){ 
                        updated += _context.SaveChanges(); 
                        Console.WriteLine(i);
                    }
                }
                return Ok(updated += _context.SaveChanges());
            }
            return BadRequest();
        }

        [HttpPost("Receipts")]
        [RequestFormLimits(MultipartBodyLengthLimit = 209715200)]
        [RequestSizeLimit(209715200)]
        public IActionResult setReceiptsData([FromForm] IFormFile file)
        {
            //Si contiene archivos 
            if(file.Length > 0){
                List<Interno.DJO.Models.Taxonomy> taxonomies = _context.Taxonomies.ToList();
                List<Interno.DJO.Models.ItemPrice> prices  = _context.ItemPrices.ToList();
                
                DataTable Report = ReportController.CSVtoDataTable( file.OpenReadStream());
                Object[] last = Report.Rows[Report.Rows.Count-1].ItemArray;

                int con = 0;
                int updated = 0;
                //int count =  _context.Database.ExecuteSqlRaw("TRUNCATE TABLE `dbinterno`.`purchasereceipts`;");
                foreach (DataRow row in Report.Rows)
                {
                    //return Ok(row);
                    // Interno.DJO.Models.PurchaseReceipts order = list.FirstOrDefault(p => 
                    //     p.PO.ToString() == row["po Number"].ToString()
                    //     && p.Line.ToString() == row["purchase Order Line Number"].ToString()
                    //     && p.ReceivedDate.ToString() == row["received Date"].ToString()
                    //     && p.ReceivedQty.ToString() == row["po Received Qty"].ToString()
                    // ) ?? new Models.PurchaseReceipts();
                    
                    var order  = new Interno.DJO.Models.PurchaseReceipts();
                    //try{
                        
                        decimal temp;
                        Decimal.TryParse(row["po Received Qty"].ToString(),out temp);
                        if(temp > 0){
                            order.SupplierName = row["supplier Name"].ToString();
                            order.VendorType = row["vendor Type"].ToString();
                            order.ProductName = row["product Name"].ToString().Replace("*","");
                            order.Product = row["*Product Number"].ToString().Replace("*","");
                            order.ProductType = row["product Type Description"].ToString();
                            order.Site =  row["site"].ToString();
                            order.POCreationDate = DateTime.Parse( row["po Creation Date"].ToString());
                            order.POReleaseDate = (row["po Release Date"].ToString()!="")?  DateTime.Parse( row["po Release Date"].ToString()) : DateTime.MinValue;
                            order.PO = Int32.Parse(row["po Number"].ToString());
                            order.Line = Int32.Parse(row["purchase Order Line Number"].ToString());
                            order.ReceivedDate = DateTime.Parse(row["received Date"].ToString());
                            order.PromisedDate = (row["promised Date"].ToString()!="")?  DateTime.Parse(row["promised Date"].ToString()) : DateTime.MinValue;
                            order.Buyer = row["buyer"].ToString();
                            order.FiscalYear = Int32.Parse( row["fiscal Year"].ToString() );
                            order.FiscalQuarter = row["fiscal Quarter"].ToString();
                            order.FiscalPeriod = row["fiscal Period"].ToString();
                            order.FiscalWeek = row["fiscal Week"].ToString();
                            order.ReceiptAmount = Decimal.Parse(row["po Received Amount"].ToString());
                            order.ReceivedQty = Decimal.Parse(row["po Received Qty"].ToString());
                            order.ReceivedPrice = (row["po Received Price"].ToString()!="")? Decimal.Parse(row["po Received Price"].ToString()) : Decimal.Zero;
                            order.POQty = (row["po Quantity"].ToString()!="")? Decimal.Parse(row["po Quantity"].ToString()) : Decimal.Zero;
                            try{
                                var price = prices.FirstOrDefault( p => p.Item == order.Product && p.Site == order.Site);
                                order.StdCost = (price != null)? Decimal.Parse( price.StdCost.ToString()) : order.ReceivedPrice;
                                order.StdCostExt = (order.StdCost != 0)? Decimal.Round(order.StdCost * order.ReceivedQty,6) : order.ReceivedPrice;
                                order.PPV = Decimal.Round((order.StdCostExt != 0)? order.ReceiptAmount - order.StdCostExt : 0,6);
                                order.Spend = Decimal.Round( order.ReceiptAmount - order.PPV,6);
                            }catch(System.NullReferenceException) { }
                            try{
                                order.Category = taxonomies.FirstOrDefault(t => t.ProductNumber == order.Product).PurchaseCategory; 
                            }catch(System.NullReferenceException){ }
                            
                            _context.PurchaseReceipts.Add(order);
                            con++;
                            if((con % 1000) == 0){
                                Console.WriteLine(con);
                                updated += _context.SaveChanges();
                            }
                            
                        }
                    // }catch(System.ArgumentException){
                    //     return BadRequest(row);
                    // }
                }return Ok(updated += _context.SaveChanges());
            } return BadRequest();
        }

        [HttpPost("BlankPOS")]
        [RequestFormLimits(MultipartBodyLengthLimit = 209715200)]
        [RequestSizeLimit(209715200)]
        public IActionResult setBlankPOSData([FromForm] IFormFile file)
        {
            
            if(file.Length > 0){
                int updated = 0;
                
                DataTable Report = ReportController.CSVtoDataTable(file.OpenReadStream());
                if(!file.FileName.Contains("Open Std POs")){
                    _context.Database.ExecuteSqlRaw("TRUNCATE TABLE `dbinterno`.`blankpos`;");
                }
                for (int i = 0; i < Report.Rows.Count; i++)
                {
                    Interno.DJO.Models.BlankPO po = new Interno.DJO.Models.BlankPO();
                    po.FOB = Report.Rows[i]["fob"].ToString();
                    po.Terms = Report.Rows[i]["terms"].ToString();
                    try{
                    po.AgreedUnitPrice = Decimal.Parse( Report.Rows[i]["agreed Unit Price"].ToString() );
                    }catch(System.ArgumentException){ 
                        po.AgreedUnitPrice = Decimal.Parse( Report.Rows[i]["unit Price"].ToString() );
                    }
                    po.BuyerName = Report.Rows[i]["buyer Name"].ToString();
                    po.CurrencyCode = Report.Rows[i]["currency Code"].ToString();
                    po.ItemDescription = Report.Rows[i]["item Description"].ToString();
                    po.Line = Int32.Parse( Report.Rows[i]["po Line Number"].ToString() );
                    po.PO = Int32.Parse( Report.Rows[i]["po Number"].ToString() );
                    try{
                        po.TypePO = Report.Rows[i]["po Type"].ToString();
                    }catch(System.ArgumentException){ po.TypePO = "Standart"; }
                    
                    po.QtyOutstanding = Decimal.Parse( Report.Rows[i]["quantity Outstanding"].ToString() );
                    try{
                    po.AmountOutstanding = Decimal.Parse( Report.Rows[i]["Quantity Outstanding * Agreed Unit Price"].ToString() );
                    }catch(System.ArgumentException){
                        po.AmountOutstanding = Decimal.Parse( Report.Rows[i]["quantity Outstanding"].ToString() ) * Decimal.Parse( Report.Rows[i]["unit Price"].ToString() );
                    }
                    try{
                        po.ReleaseAuthStatus = Report.Rows[i]["release Authorization Status"].ToString();
                    }catch(System.ArgumentException){}
                    try{
                        po.ReleaseCloseCode = Report.Rows[i]["release Closed Code"].ToString();
                    }catch(System.ArgumentException){Report.Rows[i]["closed Code"].ToString();}
                    
                    po.ReleaseNumber = (Report.Rows[i]["release Number"].ToString() != "N/A" )? Int32.Parse( Report.Rows[i]["release Number"].ToString() ) : 0;
                    try{
                        po.ShipToOrg = Report.Rows[i]["ship To Organization"].ToString();
                    }catch(System.ArgumentException){ po.ShipToOrg = Report.Rows[i]["ship To Organization Code"].ToString(); }
                    try{
                        po.ShipmentType = Report.Rows[i]["shipment Type"].ToString();
                    }catch(System.ArgumentException){}
                    po.Vendor = Report.Rows[i]["vendor Name"].ToString();
                    try{
                        po.Item = Report.Rows[i]["'*' || ITEM$Item"].ToString().Replace("*","");
                    }catch(System.ArgumentException){ po.Item = Report.Rows[i]["*Item Number"].ToString().Replace("*",""); }
                    try{
                        po.NeedByDate = (Report.Rows[i][" CAST (Need By Date AS DATE )"].ToString()!="" )? DateTime.Parse( Report.Rows[i][" CAST (Need By Date AS DATE )"].ToString()) : DateTime.MinValue;
                    }catch(System.ArgumentException){
                        po.NeedByDate = (Report.Rows[i]["need By Date"].ToString()!="" )? DateTime.Parse( Report.Rows[i]["need By Date"].ToString()) : DateTime.MinValue;
                    }
                    try{
                    po.CreationDate = (Report.Rows[i][" CAST (PO Creation Date AS DATE )"].ToString() != "")? DateTime.Parse( Report.Rows[i][" CAST (PO Creation Date AS DATE )"].ToString() ) : DateTime.MinValue;
                    }catch(System.ArgumentException){ po.CreationDate = (Report.Rows[i]["po Creation Date"].ToString() != "")? DateTime.Parse( Report.Rows[i]["po Creation Date"].ToString() ) : DateTime.MinValue; }
                    
                    try{
                        po.PromisedDate =(Report.Rows[i][" CAST (Promised Date AS DATE )"].ToString()!="" )? DateTime.Parse( Report.Rows[i][" CAST (Promised Date AS DATE )"].ToString() ) : DateTime.MinValue;
                    }catch(System.ArgumentException){ }
                    try{
                        po.ReleaseDate = DateTime.Parse( Report.Rows[i][" CAST (Release Date AS DATE )"].ToString() );
                    }catch(System.ArgumentException){ }
                    
                    _context.BlankPOs.Add(po);
                    if((i % 1000) == 0){
                        updated += _context.SaveChanges();
                    }
                    Console.WriteLine(i);
                }
                return Ok(updated += _context.SaveChanges());

            }
            return BadRequest();
        }

        [HttpPost("Quotations")]
        [RequestFormLimits(MultipartBodyLengthLimit = 209715200)]
        [RequestSizeLimit(209715200)]
        public IActionResult setQuotationsReport([FromForm] IFormFile file)
        {   
            if(file.Length > 0){       
                DataTable Report = ReportController.CSVtoDataTable(file.OpenReadStream());
                var temp = Report.AsEnumerable().Where(r => r.Field<string>("status") == "A").ToList();
                
                if(!file.FileName.Contains("Quotation")){
                    _context.Database.ExecuteSqlRaw("TRUNCATE TABLE `dbinterno`.`quotations`;");
                }
                for (int i = 0; i < temp.Count; i++)
                {
                    
                    Interno.DJO.Models.Quotation po = new Interno.DJO.Models.Quotation();
                    po.Quote = Int32.Parse(temp[i]["quotE_NUM"].ToString());
                    po.Line = Int32.Parse(temp[i]["linE_NUM"].ToString());
                    po.Item = temp[i]["item"].ToString();
                    po.Description = temp[i]["iteM_DESCRIPTION"].ToString();
                    po.Buyer = temp[i]["buyeR_ON_QUOTE"].ToString();
                    po.Creation = DateTime.Parse( temp[i]["creatioN_DATE"].ToString());
                    po.SupplierItem = temp[i]["supplieR_ITEM"].ToString();
                    po.Vendor = temp[i]["vendoR_NAME"].ToString();
                    po.VendorSite = temp[i]["vendoR_SITE_CODE"].ToString();
                    po.Status = Char.Parse( temp[i]["status"].ToString());
                    po.LastUpdate =  DateTime.Parse(temp[i]["lasT_UPDATE_DATE"].ToString());
                    po.ShipTo = temp[i]["shiP_TO"].ToString();
                    po.EefTo = temp[i]["efF_TO"].ToString();
                    po.EefFrom = temp[i]["efF_FROM"].ToString();
                    po.BillTo = temp[i]["bilL_TO"].ToString();
                    po.Term = temp[i]["terM_NAME"].ToString();
                    po.Type = temp[i]["type"].ToString();
                    po.UOM = temp[i]["uom"].ToString();
                    po.UnitPrice = Decimal.Parse(temp[i]["uniT_PRICE"].ToString());
                    
                    _context.Quotations.Add(po);
                }
                return Ok(_context.SaveChanges());
            }
            return BadRequest();
        }

        [HttpPost("Backorders")]
        [RequestFormLimits(MultipartBodyLengthLimit = 209715200)]
        [RequestSizeLimit(209715200)]
        public IActionResult setBackOrder([FromForm] IFormFile file)
        {
            if(file.Length > 0){
                if(file.FileName.Split(".xlsx").Count() > 1){
                    // int updated = 0;
                    Console.WriteLine("LoadFile"+ DateTime.Now.TimeOfDay);
                    System.Text.Encoding.RegisterProvider(System.Text.CodePagesEncodingProvider.Instance);
                    using (var reader = ExcelReaderFactory.CreateReader(file.OpenReadStream()))
                    {
                        var result = reader.AsDataSet(new ExcelDataSetConfiguration() 
                        { 
                            ConfigureDataTable = (data) => new ExcelDataTableConfiguration(){ UseHeaderRow = true } 
                        });
                        DataTable Report = result.Tables["Orders"];
                       
                        var BackOrder = Report.AsEnumerable().Where(r => r.Field<string>("final Status") == "BACKORDER" && (r.Field<string>("org") == "DFW" || r.Field<string>("org") == "TJD"));        
                        List<BackOrder> group = BackOrder.GroupBy(r => r["item"]).Select(r => new BackOrder {
                            Date = DateTime.Now.Date,
                            Item = r.Key.ToString().Replace("*",""),
                            Quantity = r.Sum( r => r.Field<double>("quantity")),
                            Amount = r.Sum( r => r.Field<double>("amount")),
                            //BOM =  _bom.Where(b => b.Component == r.Key).ToList()
                        }).OrderBy(r => r.Item).ToList();
                        List<string> _items = group.Select(g => g.Item).ToList();
                        List<BOM> _bom =  _context.BOMs.Where(b => _items.Contains(b.Component)).ToList();
                        List<BackOrder> newBackOrder = group.AsEnumerable().Where(g => _items.Contains(g.Item)).ToList();
 
                        foreach (var item in group)
                        {
                            item.BOM =  _bom.Where(b => b.Component == item.Item).GroupBy(b => b.Item).Select(b => b.FirstOrDefault()).ToList();
                            if(item.BOM.Count() > 0){
                                foreach (var comp in item.BOM)
                                {
                                    var t1 = newBackOrder.FirstOrDefault(b=> b.Item == comp.Item);
                                    if(t1 != null){
                                        comp.Backorder = t1.Amount;
                                    }   
                                }
                                item.BOMAffectedAmount =  item.BOM.Sum(b => b.Backorder);
                                
                            }
                            item.BOM = item.BOM.Where(b => b.Backorder > 0).ToList();
                            if(item.BOMAffectedAmount == 0) item.BOMAffectedAmount = item.Amount;
                        }
                        //Gravar Historial de BackOrder
                        
                        int count =  _context.Database.ExecuteSqlRaw("TRUNCATE TABLE `dbinterno`.`backorders`;");
                        foreach (var item in group.Where(b => b.BOMAffectedAmount > 0))
                        {
                            _context.BackOrders.Add(item);
                        }
                        return Ok(_context.SaveChanges());
                    }
                }else{
                    return BadRequest("No es un archivo de Excel XLSX");
                }
            }
            return BadRequest();
        }
        
        [HttpPost("MoveOrders")]
        [RequestFormLimits(MultipartBodyLengthLimit = 209715200)]
        [RequestSizeLimit(209715200)]
        public IActionResult setMoverOrders([FromForm] IFormFile file)
        {
            //Si contiene archivos 
            if(file.Length > 0){
                List<Interno.DJO.Models.MoveOrder> _orders = _context.MoveOrders.ToList();
                DataTable Report = ReportController.ExcelToDataTable( file.OpenReadStream())[0];

                for (int i = 0; i < Report.Rows.Count; i++)
                {
                    var updated = 0;
                    var ord = _orders.FirstOrDefault(o => o.Number.ToString() == Report.Rows[i]["number"].ToString() && o.Line.ToString() == Report.Rows[i]["line"].ToString())?? new Interno.DJO.Models.MoveOrder();
                    //return Ok(Report.Rows[i]);
                    try{
                        
                        ord.Number = Int64.Parse( Report.Rows[i]["number"].ToString());
                        ord.Description = Report.Rows[i]["description"].ToString();
                        ord.CreatedDateTime = (Report.Rows[i]["create Date Time"].ToString() != "")? DateTime.Parse( Report.Rows[i]["create Date Time"].ToString() ) : DateTime.MinValue;
                        ord.Type = Report.Rows[i]["type"].ToString();
                        ord.Line = (Report.Rows[i]["line"].ToString()!="")? Int32.Parse( Report.Rows[i]["line"].ToString() ) : 0;
                        ord.TransactionType = Report.Rows[i]["transaction Type"].ToString();
                        ord.Item =  Report.Rows[i]["item"].ToString();
                        ord.SourceSubinv = Report.Rows[i]["source Subinv"].ToString();
                        ord.SourceLocator = Report.Rows[i]["source Locator"].ToString();
                        ord.DestinationSubinv = Report.Rows[i]["destination Subinv"].ToString();
                        ord.DestinationLocator = Report.Rows[i]["destination Locator"].ToString().Replace("..","");
                        ord.DestinationAcoount = Report.Rows[i]["destination Account"].ToString();
                        ord.LotNumber = Report.Rows[i]["lot Number"].ToString();
                        ord.ExpirationDate = (Report.Rows[i]["expiration Date"].ToString()!="")? DateTime.Parse( Report.Rows[i]["expiration Date"].ToString() ):DateTime.MinValue;
                        ord.SerialFrom = Report.Rows[i]["serial From"].ToString();
                        ord.SerialTo = Report.Rows[i]["serial To"].ToString();
                        ord.UnitNumber = Report.Rows[i]["unit Number"].ToString();
                        ord.UOM = Report.Rows[i]["uom"].ToString();
                        ord.TransactionQty = (Report.Rows[i]["transaction Qty"].ToString()!="")? Decimal.Parse( Report.Rows[i]["transaction Qty"].ToString() ): 0;
                        ord.RequestedQty = (Report.Rows[i]["requested Qty"].ToString()!="")? Decimal.Parse( Report.Rows[i]["requested Qty"].ToString() ):0;
                        ord.TransactionDate = (Report.Rows[i]["transaction Date Time"].ToString() != "")? DateTime.Parse( Report.Rows[i]["transaction Date Time"].ToString() ): DateTime.MinValue;
                        ord.OnTimeMetric = (Report.Rows[i]["on Time Metric"].ToString()!="")?  Boolean.Parse(Report.Rows[i]["on Time Metric"].ToString()):false;
                        ord.RequiredQty = (Report.Rows[i]["required Qty"].ToString()!="")? Decimal.Parse( Report.Rows[i]["required Qty"].ToString() ):0;
                        ord.DeliveredQty = (Report.Rows[i]["delivered Qty"].ToString()!="")? Decimal.Parse( Report.Rows[i]["delivered Qty"].ToString() ):0;
                        ord.AllocatedQty = (Report.Rows[i]["allocated Qty"].ToString()!="")? Decimal.Parse( Report.Rows[i]["allocated Qty"].ToString() ) :0;
                        ord.RemainingQty = (Report.Rows[i]["remaining Quantity"].ToString()!="")? Decimal.Parse( Report.Rows[i]["remaining Quantity"].ToString() ):0;
                        ord.SecondaryUOM = Report.Rows[i]["secondary UOM"].ToString();
                        ord.SecondaryQty = (Report.Rows[i]["secondary Qty"].ToString()!="")? Decimal.Parse( Report.Rows[i]["secondary Qty"].ToString() ):0;
                        ord.SecondaryRequestedQty = (Report.Rows[i]["secondary Requested Qty"].ToString()!="")? Decimal.Parse( Report.Rows[i]["secondary Requested Qty"].ToString() ):0;
                        ord.SecondatyRequiredQty = (Report.Rows[i]["secondary Required Qty"].ToString()!="")? Decimal.Parse( Report.Rows[i]["secondary Required Qty"].ToString() ):0;
                        ord.SecondaryDeliveredQty = (Report.Rows[i]["secondary Delivered Qty"].ToString()!="")? Decimal.Parse( Report.Rows[i]["secondary Delivered Qty"].ToString() ):0;
                        ord.SecondaryAllocatedQty = (Report.Rows[i]["secondary Allocated Qty"].ToString()!="")? Decimal.Parse( Report.Rows[i]["secondary Allocated Qty"].ToString() ):0;
                        ord.Grade =  Report.Rows[i]["grade"].ToString();
                        ord.DateRequired = (Report.Rows[i]["date Required"].ToString()!="")? DateTime.Parse( Report.Rows[i]["date Required"].ToString() ): DateTime.MinValue;
                        ord.Reason = Report.Rows[i]["reason"].ToString();
                        ord.Reference = Report.Rows[i]["reference"].ToString();
                        ord.Route = Report.Rows[i]["route"].ToString();
                        ord.Cell = Report.Rows[i]["cell"].ToString();
                        ord.Priority = Report.Rows[i]["priority"].ToString();
                        ord.LineStatus = Report.Rows[i]["line Status"].ToString();
                        ord.StatusDate = (Report.Rows[i]["status Date"].ToString()!="")? DateTime.Parse( Report.Rows[i]["status Date"].ToString() ):DateTime.MinValue;
                        ord.CreatedBy = Report.Rows[i]["created By"].ToString();
                        switch (Report.Rows[i]["line Status"].ToString())
                        {
                            case "Incomplete": ord.Status = Domain.Enum.StatusType.InPart; break;
                            case "Closed": ord.Status = Domain.Enum.StatusType.Closed; break;
                            case "Canceled": ord.Status = Domain.Enum.StatusType.Canceled; break;
                            default: ord.Status = Domain.Enum.StatusType.StandBy; break;
                        }
                        if(ord.Id == 0){
                            _context.MoveOrders.Add(ord);
                        }else{
                            _context.MoveOrders.Update(ord);
                        }    
                    }
                    catch(Microsoft.EntityFrameworkCore.DbUpdateConcurrencyException){ return BadRequest(ord);}
                    catch(Microsoft.EntityFrameworkCore.DbUpdateException){}
                    catch(System.InvalidOperationException){}
                }
                return Ok(_context.SaveChanges());
            }
            return BadRequest();
        }

        [HttpPost("PlannedPOTable")]
        [RequestFormLimits(MultipartBodyLengthLimit = 209715200)]
        [RequestSizeLimit(209715200)]
        public IActionResult setPlanedPOSTable([FromForm] IFormFile file)
        {
            //Si contiene archivos 
            if(file.Length > 0){
                List<Interno.DJO.Models.Taxonomy> taxonomies = _context.Taxonomies.ToList();
                List<Interno.DJO.Models.ItemPrice> prices = _context.ItemPrices.ToList();
                
                DataTable Report = ReportController.ExcelToDataTable( file.OpenReadStream())[0];
                Object[] last = Report.Rows[Report.Rows.Count-1].ItemArray;
                
                int count =  _context.Database.ExecuteSqlRaw("TRUNCATE TABLE `dbinterno`.`plannedpos`;");
                string temp = null;
                for (int i = 2; i < Report.Rows.Count; i++)
                {
                    Interno.DJO.Models.PlannedPO pla = new PlannedPO();
                    pla.Item =(Report.Rows[i][0].ToString() != temp)? Report.Rows[i][0].ToString() : temp;
                    pla.Description = Report.Rows[i][1].ToString();
                    pla.Site = Report.Rows[i][2].ToString();
                    pla.Type = Report.Rows[i][3].ToString();
                    pla.Status = Report.Rows[i][4].ToString();
                    pla.Buyer = Report.Rows[i][5].ToString();
                    pla.Supplier = Report.Rows[i][6].ToString();
                    pla.StdCost = Decimal.Parse(Report.Rows[i][7].ToString());
                    pla.SupplyType = Report.Rows[i][8].ToString();
                    pla.Line = Int16.Parse(Report.Rows[i][9].ToString());
                    pla.EffQty = Decimal.Parse( Report.Rows[i][10].ToString().Replace(",",""));
                    pla.LeadTime = Int16.Parse( Report.Rows[i][11].ToString());
                    pla.DaysToAcc = Int16.Parse( Report.Rows[i][12].ToString());
                    pla.Action = Report.Rows[i][13].ToString();
                    pla.StartDate = DateTime.Parse( Report.Rows[i][14].ToString());
                    pla.DueDate = DateTime.Parse(Report.Rows[i][15].ToString());
                    pla.StdCostExt = pla.StdCost * pla.EffQty;
                    try{
                        var price = prices.FirstOrDefault( p => p.Item == pla.Item && p.Site == pla.Site);
                        pla.PPV = Decimal.Round((pla.StdCostExt != 0)? pla.EffQty - pla.StdCostExt : 0,6);
                        pla.Spend = Decimal.Round( pla.EffQty - pla.StdCost,6);
                    }catch(System.NullReferenceException) { }
                    try{
                        pla.Category = taxonomies.FirstOrDefault(t => t.ProductNumber == pla.Item).PurchaseCategory; 
                    }catch(System.NullReferenceException){ }
                    _context.PlannedPOs.Add(pla);
                    temp = Report.Rows[i][0].ToString();
                    Console.WriteLine(i);
                }
                return Ok(_context.SaveChanges());
            }
            return BadRequest();
        }

        [HttpPost("Completions")]
        [RequestFormLimits(MultipartBodyLengthLimit = 209715200)]
        [RequestSizeLimit(209715200)]
        public IActionResult setCompletions([FromForm] IFormFile file)
        {
            List<Interno.DJO.Models.Completion> _completions = _context.Completions.ToList();
            //Si contiene archivos 
            if(file.Length > 0){
                DataTable Report = ReportController.ExcelToDataTable( file.OpenReadStream())[0];
                
                Object[] last = Report.Rows[Report.Rows.Count-1].ItemArray;
                for (int i = 13; i < Report.Rows.Count; i++)
                {
                    /*
                        {
                        "tjm WIP Completions Report WTD": "Item Number",0
                        "column1": "Item Description",1
                        "column2": "Transaction Date",2
                        "column3": "Date",3
                        "column4": "Quantity",4
                        "column5": "Mfg. Cell",5
                        "column6": "Mfg. Cell Description",6
                        "column7": "Product Brand",7
                        "column8": "Job Number",8
                        "column9": "Item Type",9
                        "column10": "Value Stream"10
                    },*/
                    Interno.DJO.Models.Completion temp = _completions.FirstOrDefault(c => c.JobNumber == Report.Rows[i][8].ToString() && c.TransDateTime == DateTime.Parse(Report.Rows[i][2].ToString())) ?? new Completion();
                    
                    temp.Item = Report.Rows[i][0].ToString();
                    temp.Description = Report.Rows[i][1].ToString();
                    temp.TransDateTime = DateTime.Parse(Report.Rows[i][2].ToString());
                    try{
                        temp.Qty = Decimal.Parse( Report.Rows[i][4].ToString());
                    }catch(System.FormatException){ return BadRequest(Report.Rows[i][4].ToString());}
                    
                    temp.Module = Report.Rows[i][5].ToString();
                    temp.ModuleDesc = Report.Rows[i][6].ToString();
                    temp.ProductBrand = Report.Rows[i][7].ToString();
                    temp.JobNumber = Report.Rows[i][8].ToString();
                    temp.ItemType = Report.Rows[i][9].ToString();
                    temp.ValueStream = Report.Rows[i][10].ToString();
                    _context.AddOrUpdate(temp);
                }
                return Ok(_context.SaveChanges());
            }
            return BadRequest();
        }

        [HttpPost("ImportExport/BalanceOnHand")]
        [RequestFormLimits(MultipartBodyLengthLimit = 209715200)]
        [RequestSizeLimit(209715200)]
        public IActionResult setIEBlanceOnHand([FromForm] IFormFile file)
        {
            if(file.Length > 0){
                // int updated = 0;
                DataTable Report = ReportController.ExcelToDataTable(file.OpenReadStream())[0];
                _context.Database.ExecuteSqlRaw("TRUNCATE TABLE `dbinterno`.`balanceonhands`;");
                for (int i = 0; i < Report.Rows.Count; i++)
                {
                    if(Report.Rows[i]["received"].ToString() != ""){
                        BalanceOnHand row = new BalanceOnHand();
                        row.Customer = Report.Rows[i]["customer"].ToString();
                        row.ReceiveingId = (Report.Rows[i]["receivingID"].ToString() != "")? Int32.Parse(Report.Rows[i]["receivingID"].ToString()): 0;
                        row.ControlNumber = (Report.Rows[i]["controlNumber"].ToString() != "")? Int32.Parse( Report.Rows[i]["controlNumber"].ToString() ): 0;
                        row.PartNumber = Report.Rows[i]["partn"].ToString();
                        row.Description = Report.Rows[i]["descrip"].ToString().Replace("\r\n","").Replace("/"," ");
                        row.Status = Report.Rows[i]["status"].ToString().Replace("\r\n","");
                        row.Type = Report.Rows[i]["type"].ToString().Replace("\r\n","");
                        DateTime dt = DateTime.MinValue;
                        DateTime.TryParse( Report.Rows[i]["received"].ToString(), out dt);
                        row.ReceivedDate = dt;
                        row.Qty = (Report.Rows[i]["qty"].ToString() != "")? Int32.Parse( Report.Rows[i]["qty"].ToString()) : 0;
                        row.Unit = Report.Rows[i]["unit"].ToString();
                        row.DaysIn = (Report.Rows[i]["bal"].ToString() != "")? Int32.Parse( Report.Rows[i]["bal"].ToString()) : 0;
                        row.Bal = (Report.Rows[i]["bal"].ToString() != "")? Int32.Parse( Report.Rows[i]["bal"].ToString()) : 0;
                        row.Location = Report.Rows[i]["loc."].ToString();
                        row.Weight = (Report.Rows[i]["weight(lbs)"].ToString() != "")? Int32.Parse( Report.Rows[i]["weight(lbs)"].ToString() ) : 0;
                        row.Shipper = Report.Rows[i]["shipper"].ToString();
                        row.PO = Report.Rows[i]["pO#"].ToString();
                        row.Carrier = Report.Rows[i]["carrier"].ToString();
                        row.FB = Report.Rows[i]["fB#"].ToString().Replace("'","").Replace("\r\n","");
                        row.Inbond = (Report.Rows[i]["inbond#"].ToString() != "")? Int32.Parse( Report.Rows[i]["inbond#"].ToString()) : 0;
                        DateTime dt2 = DateTime.MinValue;
                        DateTime.TryParse(Report.Rows[i]["inbond Issue Date"].ToString(), out dt2);
                        row.InbondIssueDate = dt2;
                        row.Comments = Report.Rows[i]["comments"].ToString().Replace("\r\n","");
                        row.Reference = Report.Rows[i]["reference"].ToString();
                        _context.BalanceOnHands.Add(row);
                    }
                }
                return Ok(_context.SaveChanges());
            }
            return BadRequest();
        }

        [HttpPostAttribute("Score/Terms")]
        [RequestFormLimits(MultipartBodyLengthLimit = 209715200)]
        [RequestSizeLimit(209715200)]
        public IActionResult setBussinesTermsScore([FromForm] IFormFile file)
        {
            //Si contiene archivos 
            if(file.Length > 0){
                int updated = 0;
                DataTable Report = ReportController.ExcelToDataTable( file.OpenReadStream())[0];

                Object[] last = Report.Rows[Report.Rows.Count-1].ItemArray;
                
                for (int i = 0; i < Report.Rows.Count; i++) 
                {
                    var tscore = new ScoreCard{
                            KPI = "Payment Term",
                            CalculationMethod = "",
                            Target = 90,
                            FullScore = 5,
                            Frecuency = ReportFrecuency.Quarterly,
                            Category = "Business  Terms",
                            Partnership = Report.Rows[i]["supplier"].ToString().ToUpper(),
                            DataSource = "Bussines Terms Mail",
                            Performance = new List<ScorePerformance>()
                    };
                    var score  = _context.ScoreCards.FirstOrDefault(w => w.KPI == "Payment Term" && w.Partnership.ToUpper() == Report.Rows[i]["supplier"].ToString().ToUpper()) ?? tscore;
                    if(score.Id != 0){
                        score.Performance = _context.ScorePerformances.Where(w => w.ScoreCard.Id == score.Id).OrderBy(o => o.Date).ToList();
                    }
                    
                    var tDate = DateTime.Parse(Report.Rows[i]["term Date"].ToString());
                    var term = Regex.Replace(Report.Rows[i]["term"].ToString(), @"\s+", "");
                    //return Ok(new{term, term.Length, p = term.Length - 2,TErm = term.Substring(term.Length - 2,2)});
                    int tPEr = 0;
                    try{
                        tPEr = Int16.Parse( term.Substring(term.Length - 2,2));
                    }catch(System.FormatException){ }

                    if(score.Performance.Any(p => p.Date == tDate)){
                        foreach (var item in score.Performance)
                        {
                            if(item.Date == tDate)
                            {
                                item.Performance = tPEr;
                                item.Score = this.getPaymentTermsScore(term);
                            }
                        }
                    }else{
                        for (int j = 0; j < tDate.Month; j++)
                        {
                            var perfor = new ScorePerformance {  
                                Score = this.getPaymentTermsScore(term),
                                Performance = tPEr,
                                Date = tDate.AddMonths(-j),
                                Partnership = Report.Rows[i]["supplier"].ToString().ToUpper()
                            };
                            score.Performance.Add(perfor); 
                        }
                        
                    }
                    _context.ScoreCards.Update(score);
                    
                    var tscore1 = new ScoreCard{
                            KPI = "Shipping Term",
                            CalculationMethod = "",
                            Target = 90,
                            FullScore = 5,
                            Frecuency = ReportFrecuency.Quarterly,
                            Category = "Business  Terms",
                            Partnership = Report.Rows[i]["supplier"].ToString().ToUpper(),
                            DataSource = "Bussines Terms Mail",
                            Performance = new List<ScorePerformance>()
                    };
                    var score1  = _context.ScoreCards.FirstOrDefault(w => w.KPI == "Shipping Term" && w.Partnership.ToUpper() == Report.Rows[i]["supplier"].ToString().ToUpper()) ?? tscore1;
                    
                    if(score1.Id != 0){
                        score1.Performance = _context.ScorePerformances.Where(w => w.ScoreCard.Id == score1.Id).OrderBy(o => o.Date).ToList();
                    }
                    
                    
                    
                    if(Report.Rows[i]["shipping Score"].ToString() != ""){
                        var tss = Int16.Parse( Math.Round( Decimal.Parse(Report.Rows[i]["shipping Score"].ToString()) ).ToString());
                        //return Ok(new{term, term.Length, p = term.Length - 2,TErm = term.Substring(term.Length - 2,2)});
                        if(score1.Performance.Any(p => p.Date == tDate)){
                            foreach (var item in score1.Performance)
                            {
                                if(item.Date == tDate)
                                {
                                    item.Score = tss;
                                }
                            }
                        }else{
                            for (int j = 0; j < tDate.Month; j++)
                            {
                                var perfor = new ScorePerformance { 
                                    Score = tss,
                                    Date = tDate.AddMonths(-j),
                                    Partnership = Report.Rows[i]["supplier"].ToString().ToUpper()
                                };
                                score1.Performance.Add(perfor);
                            }
                        }
                    }
                    _context.ScoreCards.Update(score1);

                    updated += _context.SaveChanges();
                    
                }
                
                return Ok(updated);
            }
            return BadRequest();
        }

        [HttpPostAttribute("Score/Enginnering")]
        [RequestFormLimits(MultipartBodyLengthLimit = 209715200)]
        [RequestSizeLimit(209715200)]
        public IActionResult setEnginneringScore([FromForm] IFormFile file)
        {
            //Si contiene archivos 
            if(file.Length > 0){
                int updated = 0;
                DataTable Report = ReportController.ExcelToDataTable( file.OpenReadStream())[0];

                Object[] last = Report.Rows[Report.Rows.Count-1].ItemArray;
                
                for (int i = 0; i < Report.Rows.Count; i++)
                {
                    var tscore = new ScoreCard{
                            KPI = Report.Rows[i]["kpi"].ToString(),
                            CalculationMethod = "",
                            Target = 0,
                            FullScore = Int16.Parse(Report.Rows[i]["fullscore"].ToString()),
                            Frecuency = ReportFrecuency.Quarterly,
                            Category = "Engineering",
                            Partnership = Report.Rows[i]["supplier"].ToString().ToUpper(),
                            DataSource = "Engineering Scorecard Mail Sam",
                            Performance = new List<ScorePerformance>()
                    };
                    var score  = _context.ScoreCards.FirstOrDefault(w => w.KPI == Report.Rows[i]["kpi"].ToString() && w.Partnership.ToUpper() == Report.Rows[i]["supplier"].ToString().ToUpper()) ?? tscore;
                    if(score.Id != 0){
                        score.Performance = _context.ScorePerformances.Where(w => w.ScoreCard.Id == score.Id).OrderBy(o => o.Date).ToList();
                    }
                    
                    var tDate = InternoExtensions.GetLastDayOfMonth( DateTime.Parse(Report.Rows[i]["date"].ToString()) );
                    var performanceQ2 = Decimal.Round( Decimal.Parse(Report.Rows[i]["score"].ToString()),1);

                    if(score.Performance.Any(p => p.Date == tDate)){
                        foreach (var item in score.Performance)
                        {
                            if(item.Date == tDate)
                            {
                                item.Score = Int16.Parse(Decimal.Round( Decimal.Parse(Report.Rows[i]["score"].ToString())).ToString());
                            }
                        }
                    }else{
                        for (int j = 0; j < tDate.Month; j++)
                        {
                            var perfor = new ScorePerformance { 
                                Score = Int16.Parse(Decimal.Round( Decimal.Parse(Report.Rows[i]["score"].ToString())).ToString()),
                                Date = tDate.AddMonths(-j),
                                Partnership = Report.Rows[i]["supplier"].ToString().ToUpper()
                            };
                            score.Performance.Add(perfor);
                        }
                    }
                    _context.ScoreCards.Update(score);
                    
                   updated+= _context.SaveChanges();
                }
                return Ok(updated);
            }
            return BadRequest();
        }

        [HttpPostAttribute("Score/Quality")]
        [RequestFormLimits(MultipartBodyLengthLimit = 209715200)]
        [RequestSizeLimit(209715200)]
        public IActionResult setQualityScore([FromForm] IFormFile file)
        {
            //Si contiene archivos 
            if(file.Length > 0){
                int updated = 0;
                DataTable Report = ReportController.ExcelToDataTable( file.OpenReadStream())[0];
                Object[] last = Report.Rows[Report.Rows.Count-1].ItemArray;
                
                for (int i = 0; i < Report.Rows.Count; i++)
                {
                    var tscore = new ScoreCard{
                            KPI = "SCAR",
                            CalculationMethod = "No of SCAR",
                            Target = 0,
                            FullScore = 10,
                            Frecuency = ReportFrecuency.Quarterly,
                            Category = "Quality",
                            Partnership = Report.Rows[i]["supplier Name"].ToString().ToUpper(),
                            DataSource = "Vendor Scorecard",
                            Performance = new List<ScorePerformance>()
                    };
                    var score  = _context.ScoreCards.FirstOrDefault(w => w.KPI == "SCAR" && w.Partnership.ToUpper() == Report.Rows[i]["supplier Name"].ToString().ToUpper()) ?? tscore;
                    if(score.Id != 0){
                        score.Performance = _context.ScorePerformances.Where(w => w.ScoreCard.Id == score.Id).OrderBy(o => o.Date).ToList();
                    }

                    if(!string.IsNullOrEmpty( Report.Rows[i]["q4 Scar Date"].ToString()) &&
                        !string.IsNullOrEmpty(Report.Rows[i]["q4 Scar"].ToString()))
                    {
                        var tDate = InternoExtensions.GetLastDayOfMonth( DateTime.Parse(Report.Rows[i]["q4 Scar Date"].ToString()));
                        var performanceQ4 = Decimal.Round( Decimal.Parse(Report.Rows[i]["q4 Scar"].ToString()),1)*100;
                        
                        if(score.Performance.Any(p => p.Date == tDate)){
                            foreach (var item in score.Performance)
                            {
                                if(item.Date == tDate || item.Date == tDate.AddMonths(-1) || item.Date == tDate.AddMonths(-2))
                                {
                                    item.Performance = Decimal.Round(performanceQ4,2);
                                    item.Score = this.getQualityScarScore(performanceQ4);
                                }
                            }
                        }else{
                            for (int j = 0; j < 3; j++)
                            {
                                var perfor = new ScorePerformance { 
                                    Performance = Decimal.Round(performanceQ4,2) ,
                                    Score = this.getQualityScarScore(performanceQ4),
                                    Date = tDate.AddMonths(-j),
                                    Partnership = Report.Rows[i]["supplier Name"].ToString().ToUpper()
                                };
                                score.Performance.Add(perfor);
                            }
                        }
                        
                    }

                    if(!string.IsNullOrEmpty( Report.Rows[i]["q3 Scar Date"].ToString()) &&
                        !string.IsNullOrEmpty(Report.Rows[i]["q3 Scar"].ToString()))
                    {
                        var tDate = InternoExtensions.GetLastDayOfMonth( DateTime.Parse(Report.Rows[i]["q3 Scar Date"].ToString()));
                        var performanceQ3 = Decimal.Round( Decimal.Parse(Report.Rows[i]["q3 Scar"].ToString()),1)*100;
                        
                        if(score.Performance.Any(p => p.Date == tDate)){
                            foreach (var item in score.Performance)
                            {
                                if(item.Date == tDate || item.Date == tDate.AddMonths(-1) || item.Date == tDate.AddMonths(-2))
                                {
                                    item.Performance = Decimal.Round(performanceQ3,2);
                                    item.Score = this.getQualityScarScore(performanceQ3);
                                }
                            }
                        }else{
                            for (int j = 0; j < 3; j++)
                            {
                                var perfor = new ScorePerformance { 
                                    Performance = Decimal.Round(performanceQ3,2) ,
                                    Score = this.getQualityScarScore(performanceQ3),
                                    Date = tDate.AddMonths(-j),
                                    Partnership = Report.Rows[i]["supplier Name"].ToString().ToUpper()
                                };
                                score.Performance.Add(perfor);
                            }
                        }
                        
                    }
                    
                    if(!string.IsNullOrEmpty( Report.Rows[i]["q2 Scar Date"].ToString()) &&
                        !string.IsNullOrEmpty(Report.Rows[i]["q2 Scar"].ToString()))
                    {
                        var tDate = InternoExtensions.GetLastDayOfMonth(  DateTime.Parse(Report.Rows[i]["q2 Scar Date"].ToString()));
                        var performanceQ2 = Decimal.Round( Decimal.Parse(Report.Rows[i]["q2 Scar"].ToString()),1)*100;

                        if(score.Performance.Any(p => p.Date == tDate)){
                            foreach (var item in score.Performance)
                            {
                                if(item.Date == tDate || item.Date == tDate.AddMonths(-1) || item.Date == tDate.AddMonths(-2))
                                {
                                    item.Performance = Decimal.Round(performanceQ2,2);
                                    item.Score = this.getQualityScarScore(performanceQ2);
                                }
                            }
                        }else{
                            for (int j = 0; j < 3; j++)
                            {
                                var perfor = new ScorePerformance { 
                                    Performance = Decimal.Round(performanceQ2,2) ,
                                    Score = this.getQualityScarScore(performanceQ2),
                                    Date = tDate.AddMonths(-j),
                                    Partnership = Report.Rows[i]["supplier Name"].ToString().ToUpper()
                                };
                                score.Performance.Add(perfor);
                            }
                        }
                    }
                    
                   
                    if(!string.IsNullOrEmpty(Report.Rows[i]["q1 Scar Date"].ToString()) &&
                        !string.IsNullOrEmpty(Report.Rows[i]["q1 Scar"].ToString()))
                    {
                        var tDate1 = InternoExtensions.GetLastDayOfMonth(  DateTime.Parse(Report.Rows[i]["q1 Scar Date"].ToString()));
                        var performanceQ1 = Decimal.Round( Decimal.Parse(Report.Rows[i]["q1 Scar"].ToString()),1)*100;

                        if(score.Performance.Any(p => p.Date == tDate1)){
                            foreach (var item in score.Performance)
                            {
                                if(item.Date == tDate1 || item.Date == tDate1.AddMonths(-1) || item.Date == tDate1.AddMonths(-2))
                                {
                                    item.Performance = Decimal.Round(performanceQ1,2);
                                    item.Score = this.getQualityScarScore(performanceQ1);
                                }
                            }
                        }else{
                            for (int j = 0; j < 3; j++)
                            {
                                var perfor = new ScorePerformance { 
                                    Performance = Decimal.Round(performanceQ1,2) ,
                                    Score = this.getQualityScarScore(performanceQ1),
                                    Date = tDate1.AddMonths(-j),
                                    Partnership = Report.Rows[i]["supplier Name"].ToString().ToUpper()
                                };
                                score.Performance.Add(perfor);
                            }
                            
                        }
                    }
                    score.Partnership = Report.Rows[i]["supplier Name"].ToString().ToUpper();

                    _context.ScoreCards.Update(score);
                    
                   updated+= _context.SaveChanges();

                   //Pendiente Quality PERFORMANCE
                   var t1score = new ScoreCard{
                            KPI = "Performance",
                            CalculationMethod = "No of SCAR",
                            Target = 0,
                            FullScore = 10,
                            Frecuency = ReportFrecuency.Quarterly,
                            Category = "Quality",
                            Partnership = Report.Rows[i]["supplier Name"].ToString().ToUpper(),
                            DataSource = "Vendor Scorecard",
                            Performance = new List<ScorePerformance>()
                    };
                    var score1 = _context.ScoreCards.FirstOrDefault(w => w.KPI == "Performance" && w.Partnership.ToUpper() == Report.Rows[i]["supplier Name"].ToString().ToUpper()) ?? t1score;
                    if(score1.Id != 0){
                        score1.Performance = _context.ScorePerformances.Where(w => w.ScoreCard.Id == score1.Id).OrderBy(o => o.Date).ToList();
                    }

                    if(!string.IsNullOrEmpty( Report.Rows[i]["q4 Performance Date"].ToString()) &&
                        !string.IsNullOrEmpty(Report.Rows[i]["q4 Performance"].ToString()))
                    {
                        var tDate = InternoExtensions.GetLastDayOfMonth( DateTime.Parse(Report.Rows[i]["q4 Performance Date"].ToString()));
                        var performanceQ4 = Decimal.Round( Decimal.Parse(Report.Rows[i]["q4 Performance"].ToString()),1)*100;

                        if(score1.Performance.Any(p => p.Date == tDate)){
                            foreach (var item in score1.Performance)
                            {
                                if(item.Date == tDate || item.Date == tDate.AddMonths(-1) || item.Date == tDate.AddMonths(-2))
                                {
                                    item.Performance = Decimal.Round(performanceQ4,2);
                                    item.Score = this.getQualityPerformanceScore(performanceQ4);
                                }
                            }
                        }else{
                            for (int j = 0; j < 3; j++)
                            {
                                var perfor = new ScorePerformance { 
                                    Performance = Decimal.Round(performanceQ4,2) ,
                                    Score = this.getQualityPerformanceScore(performanceQ4),
                                    Date = tDate.AddMonths(-j),
                                    Partnership = Report.Rows[i]["supplier Name"].ToString().ToUpper()
                                };
                                score1.Performance.Add(perfor);
                            }
                        }
                    }

                    if(!string.IsNullOrEmpty( Report.Rows[i]["q3 Performance Date"].ToString()) &&
                        !string.IsNullOrEmpty(Report.Rows[i]["q3 Performance"].ToString()))
                    {
                        var tDate = InternoExtensions.GetLastDayOfMonth( DateTime.Parse(Report.Rows[i]["q3 Performance Date"].ToString()));
                        var performanceQ3 = Decimal.Round( Decimal.Parse(Report.Rows[i]["q3 Performance"].ToString()),1)*100;

                        if(score1.Performance.Any(p => p.Date == tDate)){
                            foreach (var item in score1.Performance)
                            {
                                if(item.Date == tDate || item.Date == tDate.AddMonths(-1) || item.Date == tDate.AddMonths(-2))
                                {
                                    item.Performance = Decimal.Round(performanceQ3,2);
                                    item.Score = this.getQualityPerformanceScore(performanceQ3);
                                }
                            }
                        }else{
                            for (int j = 0; j < 3; j++)
                            {
                                var perfor = new ScorePerformance { 
                                    Performance = Decimal.Round(performanceQ3,2) ,
                                    Score = this.getQualityPerformanceScore(performanceQ3),
                                    Date = tDate.AddMonths(-j),
                                    Partnership = Report.Rows[i]["supplier Name"].ToString().ToUpper()
                                };
                                score1.Performance.Add(perfor);
                            }
                        }
                    }

                    if(!string.IsNullOrEmpty( Report.Rows[i]["q2 Performance Date"].ToString()) &&
                        !string.IsNullOrEmpty(Report.Rows[i]["q2 Performance"].ToString()))
                    {
                        var tDate = InternoExtensions.GetLastDayOfMonth( DateTime.Parse(Report.Rows[i]["q2 Performance Date"].ToString()));
                        var performanceQ2 = Decimal.Round( Decimal.Parse(Report.Rows[i]["q2 Performance"].ToString()),1)*100;

                        if(score1.Performance.Any(p => p.Date == tDate)){
                            foreach (var item in score1.Performance)
                            {
                                if(item.Date == tDate || item.Date == tDate.AddMonths(-1) || item.Date == tDate.AddMonths(-2))
                                {
                                    item.Performance = Decimal.Round(performanceQ2,2);
                                    item.Score = this.getQualityPerformanceScore(performanceQ2);
                                }
                            }
                        }else{
                            for (int j = 0; j < 3; j++)
                            {
                                var perfor = new ScorePerformance { 
                                    Performance = Decimal.Round(performanceQ2,2) ,
                                    Score = this.getQualityPerformanceScore(performanceQ2),
                                    Date = tDate.AddMonths(-j),
                                    Partnership = Report.Rows[i]["supplier Name"].ToString().ToUpper()
                                };
                                score1.Performance.Add(perfor);
                            }
                        }
                    }
                    
                    if(!string.IsNullOrEmpty(Report.Rows[i]["q1 Performance Date"].ToString()) &&
                        !string.IsNullOrEmpty(Report.Rows[i]["q1 Performance"].ToString()))
                    {
                        var tDate1 = InternoExtensions.GetLastDayOfMonth( DateTime.Parse(Report.Rows[i]["q1 Performance Date"].ToString()));
                        var performanceQ1 = Decimal.Round( Decimal.Parse(Report.Rows[i]["q1 Performance"].ToString()),1)*100;

                        if(score1.Performance.Any(p => p.Date == tDate1)){
                            foreach (var item in score1.Performance)
                            {
                                if(item.Date == tDate1 || item.Date == tDate1.AddMonths(-1) || item.Date == tDate1.AddMonths(-2))
                                {
                                    item.Performance = Decimal.Round(performanceQ1,2);
                                    item.Score = this.getQualityPerformanceScore(performanceQ1);
                                }
                            }
                        }else{
                            for (int j = 0; j < 3; j++)
                            {
                                var perfor = new ScorePerformance { 
                                    Performance = Decimal.Round(performanceQ1,2) ,
                                    Score = this.getQualityPerformanceScore(performanceQ1),
                                    Date = tDate1.AddMonths(-j),
                                    Partnership = Report.Rows[i]["supplier Name"].ToString().ToUpper()
                                };
                                score1.Performance.Add(perfor);
                            }
                        }
                    }
                    
                    score1.Partnership = Report.Rows[i]["supplier Name"].ToString().ToUpper();
                   _context.ScoreCards.Update(score1);
                    
                   updated+= _context.SaveChanges();
                }
                return Ok(updated);
            }
            return BadRequest();
        }
        
        private int getPaymentTermsScore(string term)
        {
            switch ((term.Substring(term.Length - 2,2)))
            {
                case "15": return 0;
                case "30": return 1;
                case "45": return 2;
                case "60": return 3;
                case "75": return 4;
                case "90": return 5;
                default: return -1;
            } 
        }
        private int getQualityPerformanceScore(decimal val)
        {
            
            string score = Decimal.Round(val,1).ToString();
            Console.WriteLine(score);
            switch (score)
            {   
                case "100.0": return 15;
                case "99.9": return 14;
                case "99.8": return 13;
                case "99.7": return 12;
                case "99.6": return 11;
                case "99.5": return 10;
                case "99.4": return 9;
                case "99.3": return 8;
                case "99.2": return 7;
                case "99.1": return 6;
                case "99.0": return 5;
                case "98.9": return 4;
                case "98.8": return 3;
                case "98.7": return 2;
                case "98.6": return 1;
                default: return 0; 
            }
        }
        private int getQualityScarScore(decimal val)
        {
            var t = Int16.Parse(Decimal.Round(val).ToString());
            switch (t)
            {
                case 100: return 15;
                case 99: return 10;
                case 98: return 5;
                default: return 0;
            }   
        }

        


        public static DataTableCollection ExcelToDataTable(Stream stream)
        {
            System.Text.Encoding.RegisterProvider(System.Text.CodePagesEncodingProvider.Instance);
            using (var reader = ExcelReaderFactory.CreateReader(stream))
            {
                var result = reader.AsDataSet(new ExcelDataSetConfiguration()
                {
                    ConfigureDataTable = (data) => new ExcelDataTableConfiguration(){ UseHeaderRow = true }
                });
                return result.Tables;
            }
        }

        public static DataTable CSVtoDataTable(Stream stream)
        {
            using (var reader = new StreamReader(stream))
            {
                using (var csv = new CsvReader(reader,CultureInfo.InvariantCulture))
                {
                    using (var dr = new CsvDataReader(csv))
                    {        
                        var dt = new DataTable();
                        dt.Load(dr);
                        return dt;
                    }
                }
            }
        }
    }
}