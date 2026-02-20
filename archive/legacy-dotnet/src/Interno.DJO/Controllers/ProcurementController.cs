using System;
using System.Linq;

using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Http;

using System.IO;
using System.Data;
using System.Collections.Generic;
using System.Globalization;
using Interno.DJO.Models;
using Interno.DJO.Helpers;
using CsvHelper;

namespace Interno.DJO.Controllers
{
    [Route("[controller]")]
    [ApiController]
    public class ProcurementController : ControllerBase
    {
        private readonly DJOContext _context;
        CultureInfo provider = CultureInfo.InvariantCulture;
        public ProcurementController(DJOContext context) { _context = context; }

        //Metodo que compara los BOM de dos items y regresa las exepciones
        [HttpGet("BOM/Compare/{items}")]
        public IActionResult getBOM(string items)
        {
            
            List<BOM> bom1  = _context.BOMs.Where(r => r.Item == "11-3503-5").ToList();
            List<string> comp = bom1.Select(b => b.Component).ToList();
            List<BOM> bom2  = _context.BOMs.Where(r => r.Item == "11-3503-6").ToList();
            List<BOM> exc = bom2.Where(b => !comp.Contains(b.Component)).OrderBy(b => b.Id).ToList();
            List<string> comp2 = exc.Select(b => b.Component).ToList();
            foreach (var item in comp2)
            {
                comp.Add(item);
            }
            List<SupplyDemand> demand = _context.SupplyDemands.Where(s => comp.Contains(s.Item)).ToList();
            foreach (var item in exc)
            {
                item.SupplyDemand = demand.Where(d => d.Item == item.Component).ToList();
            }
            return Ok(exc);
        }
        
        [HttpGet("STBL")]
        public IActionResult getSTBLReport(){
            List<string> filter = new List<string>{"PUR","PUR-SEMI","RW","PROS"};
            List<STBLOnHandBuildReport> stbl = _context.STBLOnHandBuildReports.Where(r => r.RoutCauses == "No Inventory to Build" ).OrderBy(r => r.RequestDate).ToList();
            //return Ok(stbl);
            //Agrupamos Parent Items List
            List<string> items = stbl.GroupBy(r => r.PartName).Select(r => r.Key).ToList();
            
            //Explotamos el BOM de los Items en el Listado
            List<BOM> boms = _context.BOMs.Where(b => items.Contains(b.Item)).OrderBy(b => b.Id).ToList();
            
            //Filtramos por Componentes
            List<string> components = boms.GroupBy(b => b.Component).Select(c=> c.Key).ToList();
            //Supply Demand
            List<SupplyDemand> demand = _context.SupplyDemands.Where(s => components.Contains(s.Item)).ToList();
            //Revisamos el OpenSummary Report por Componente
            List<OpenSummaryReport> summary = _context.OpenSummaryReports.Where(s => components.Contains(s.Part) || items.Contains(s.Part)).ToList();
            foreach (var item in stbl)
            {
                item.BOM = boms.Where(b => b.Item == item.PartName).OrderBy(b => b.Component).ToList();
                if(item.BOM.Count > 0){
                    
                    foreach (var comp in item.BOM)
                    {
                        comp.SupplyDemand =  demand.Where(d => d.Item == comp.Component).ToList();
                        if(comp.SupplyDemand.Count > 0 ) {
                            foreach (var pos in comp.SupplyDemand)
                            {
                                pos.OpenSummaryReport = summary.Where(s => s.Part == pos.Item).OrderBy(s => s.DueDate).FirstOrDefault();
                                if(pos.OpenSummaryReport != null){
                                    item.ComponentDueDate = pos.OpenSummaryReport.DueDate ;
                                    item.Component = pos.OpenSummaryReport.Part;
                                    item.Supplier =  pos.OpenSummaryReport.SupplierDescription;   
                                }
                            }
                        }else{
                            var OpenSummaryReport = summary.Where(s => s.Part == comp.Component).OrderBy(s => s.DueDate).FirstOrDefault();
                            if(OpenSummaryReport != null){
                                item.ComponentDueDate = OpenSummaryReport.DueDate ;
                                item.Component = OpenSummaryReport.Part;
                                item.Supplier =  OpenSummaryReport.SupplierDescription;
                                item.Notes = "RM "+item.Component+" "+item.ComponentDueDate.Date.ToString("MM/dd"); 
                            }
                        }
                    }
                }
                item.BOM = item.BOM.Where(b => b.SupplyDemand.Count > 0).ToList();
                item.ComponentAffect = item.BOM.Where(b => b.DueDate == item.BOM.Max( b=> b.DueDate)).FirstOrDefault();
            }
            foreach (var item in stbl)
            {
                /*
                if(item.ComponentAffect != null){
                    item.NotesData = new ISTBLComp();
                    item.NotesData.Comp = item.ComponentAffect.Component;
                    item.NotesData.DueDate = item.ComponentAffect.DueDate;
                    if(item.ComponentAffect.SupplyDemand.FirstOrDefault().Type != null){
                        item.NotesData.Type = item.ComponentAffect.SupplyDemand.FirstOrDefault().Type;
                        item.Supplier = item.ComponentAffect.SupplyDemand.FirstOrDefault().Supplier;
                    }
                }
                if(item.NotesData != null){
                    item.Component = item.NotesData.Comp;
                    item.ComponentDueDate = item.NotesData.DueDate;
                    item.Notes = item.NotesData.Type+" "+item.NotesData.Comp+" "+item.NotesData.DueDate.Date.ToString("MM/dd"); 
                }
                /*
                if(item.BOM.Count == 0){
                    var OpenSummaryReport = summary.Where(s => s.Part == item.PartName).OrderBy(s => s.DueDate).FirstOrDefault();
                    if(OpenSummaryReport != null){
                        item.Component = OpenSummaryReport.Part;
                        item.ComponentDueDate = OpenSummaryReport.DueDate;
                        item.Supplier = OpenSummaryReport.Supplier;
                    }
                }*/
                _context.STBLOnHandBuildReports.Update(item);
            }
            _context.SaveChanges();
            //Generamos el documento
            var stream = new MemoryStream();
            //Escribimos en el Documento
            using(var writeFile = new StreamWriter(stream, leaveOpen: true)) {
                var csv = new CsvWriter(writeFile, provider);
                //csv.Configuration.RegisterClassMap<GroupReportCSVMap>();            
                csv.WriteRecords(stbl.Select(s => new{
                    s.PartName,s.Description,s.Site,s.Type,s.SourceType,s.Source,s.Buyer,s.Cell,s.OrderType,s.Status,
                    s.DemandPlanSegment,s.OrderLine,s.CorporateBrand,s.RequestDate,s.ShortCompCount,s.Hold,s.Quantity,s.UnitSellingPrice,s.ExtValue,
                    s.FGOnHandQty,s.OnHandBuildQty,s.QtyOnWorngOrg,s.TotalBuildQuantity,s.STBLQtyInpanct,s.NetOH,s.RoutCauses,s.Notes,s.Supplier,s.Component,s.ComponentDueDate,s.Category,s.Module}));
            }
            stream.Position = 0; //reset stream
            //Regresamos Documento CSV
            return File(stream, "application/octet-stream", "STBL"+DateTime.Now.Date.ToString()+".csv");
            
            //return Ok(stbl);
        }
    
        //Metodo que calcula el STBL para el scorcard de Procurement
        [HttpGet("ScoreCard/STBL")]
        public IActionResult CalculateSTBL()
        {
            var now = DateTime.Now.Date;
             
            List<STBLOnHandBuildReport> stbl = _context.STBLOnHandBuildReports.Where(r => r.RoutCauses == "No Inventory to Build" ).OrderBy(r => r.RequestDate).ToList();
            
            var Receipts = _context.PurchaseReceipts.Where(r => r.ReceivedDate.Month == now.Month && r.ReceivedDate.Year == now.Year);
            //return Ok(new{Min = Receipts.Min(r => r.ReceivedDate), Max = Receipts.Max(r => r.ReceivedDate)});
            
            var temp = stbl.GroupBy(g => g.Supplier).Select(s => new {
                Supplier = s.Key, 
                MfgPfg = s.GroupBy(s => s.MfgPfg).Select(s => new{Type = s.Key, Sum = s.Sum(s => s.STBLQtyInpanct)}),
                STBL = s.Sum(s => s.STBLQtyInpanct)*-1,
                Receipts = Receipts.Where(r => r.SupplierName == s.Key).Sum(s => s.ReceivedQty),
                DaysOfShortage = (Receipts.Where(r => r.SupplierName == s.Key).Sum(s => s.ReceivedQty) != 0 && s.Sum(s => s.STBLQtyInpanct) != 0)? 
                    (s.Sum(s => s.STBLQtyInpanct)*-1) *22 / Receipts.Where(r => r.SupplierName == s.Key).Sum(s => s.ReceivedQty)
                    : 0
            });
            
            
            List<ScorePerformance> supliersSTBL = new List<ScorePerformance>();

            foreach (var item in temp)
            {
                supliersSTBL.Add( new ScorePerformance{
                    Partnership = item.Supplier,
                    Date = InternoExtensions.GetLastDayOfMonth(now),
                    Performance = item.DaysOfShortage,
                    Score = (item.DaysOfShortage >= 0 && item.DaysOfShortage <4)? 15 - (Int16.Parse( Math.Round(item.DaysOfShortage).ToString())*5) : 0
                });
            }
            
            foreach (var item in supliersSTBL.Where(w => w.Partnership != null))
            {
                List<ScorePerformance> list = new List<ScorePerformance>();
                list.Add(item);
                ScoreCard score = new ScoreCard{
                    KPI = "STBL (Days of Shortage)",
                    CalculationMethod =  "Sum(STBLQtyInpact)*22 / Sum(ReceiptsQty)",
                    Target = 0,
                    FullScore = 15,
                    Frecuency = ReportFrecuency.Monthly,
                    Category = "Delivery",
                    Partnership = item.Partnership,
                    Performance = list,
                    DataSource = "STBL OnHand Build Report"
                };
                
                _context.AddOrUpdate(score);
                
            }
            return Ok(_context.SaveChanges());
        }

        [HttpGet("Demand")]
        public IActionResult getProcurementDemand()
        {
            
            var demand = _context.SupplyDemands.ToList();
            List<string> _items = demand.GroupBy(d => d.Item).Select(r => r.Key).ToList();
            List<BOM> _boms = _context.BOMs.Where(b => _items.Contains(b.Component)).ToList();
            List<string> parents = _boms.GroupBy(b => b.Item).Select(b => b.Key).ToList();
            _boms = _context.BOMs.Where(b => parents.Contains(b.Item)).ToList();
            List<string> components = _boms.GroupBy(b => b.Component).Select(b => b.Key).ToList();
            List<OpenSummaryReport> _summary = _context.OpenSummaryReports.Where(sr => components.Contains(sr.Part)).ToList();

            List<ProjectedDate> _dates = _context.ProjectedDates.ToList();
            
            foreach (var item in demand)
            {
                item.ProjectedDates = _dates.Where(pd => pd.SupplyDemand.Id == item.Id).OrderBy(r => r.Date).ToList();
                item.BOM = _boms.Where(b => b.Component ==  item.Item).ToList();
                foreach (var comp in item.BOM)
                {
                    var temp = _summary.Where(s => s.Part == comp.Component).OrderByDescending(s => s.DueDate);
                    comp.OpenSummaryReport = (temp.Count() > 0)? temp.First() : null;
                    if(comp.OpenSummaryReport != null){ comp.DueDate = comp.OpenSummaryReport.DueDate; }
                }
                var t1 = item.BOM.Where(b => b.OpenSummaryReport != null).OrderByDescending(s => s.OpenSummaryReport.DueDate);
                item.BOM = null;
                if(t1.Count() > 0){
                    item.OpenSummaryReport = t1.First().OpenSummaryReport;
                    item.DueDate = item.OpenSummaryReport.DueDate;
                }
                item.ProjectedDates = item.ProjectedDates.Where(pd => pd.Date >= item.DueDate).ToList();
                var t2 = item.ProjectedDates.Where(pd => pd.Date < item.DueDate).OrderByDescending(r => r.Date);
                if(t2.Count() > 0){ item.Week = t2.First().Week;};
            }
            return Ok(new{Total =demand.Count,Short = demand.Where(b => b.Week >0).Count(),Demand = demand.OrderBy(d => d.DueDate)});
        }

        [HttpGet("QuotationPrice")]
        public IActionResult getQuotationsPrice(){
            // return Ok(_context.Quotations.ToList().GroupBy(g => new {g.Item, g.Vendor,g.VendorSite}).Select(s => new{ s.Key.Item, s.Key.Vendor, s.Key.VendorSite,Quote = s.First().Quote,Price = s.First().UnitPrice, Updated = s.First().LastUpdate}).Join(
            //     _context.OpenSummaryReports, qo => qo.Item , po => po.Part, (qo,po) => {
            //         po.Part,
                    
            //     }
            // ));

            // .Join(_context.BOMs, Wo => Wo.FinishItemCode,bom => bom.Component, (wo,bom) => new{
            //             Item = wo.FinishItemCode,
            //             Module = bom.ComponentModule,
            //             Type = bom.ComponentType,
            //             WO = wo
            //         })
            return BadRequest();
        }
        
        //Metodo que calcula el Scorecard de los Suppliers
        [HttpGet("CalculateScore")]
        public IActionResult calcualteScore()
        {
            DateTime fecha = new DateTime(DateTime.Now.Year-1,12,1);//First Day of Actual Year
            

            int updated = 0;
            var lastdate = InternoExtensions.GetLastDayOfMonth(DateTime.Now);
            
            //-- OTD --
            // //Cargamos informacion de OTD desde el Anio en Curso
            List<OTDReceipt> _otd = _context.OTDReceipts.Where(w => w.ReceiptCreationDate >= fecha && w.ReceiptCreationDate < lastdate).ToList();
            
            //Agrupamos informacion para el ScoreCard
            var groupOTD = _otd.GroupBy(o => new{o.Vendor,Period = InternoExtensions.GetLastDayOfMonth(o.ReceiptCreationDate)}).Select(s => 
            new ScorePerformance { 
                    //Orders = s.Count(), 
                    //Late = s.Where(r => r.OnTime == false).Count(),
                    Performance = 100 - (s.Where(r => r.OnTime == false).Count()*100)/s.Count(),
                    Score = ((100 - (s.Where(r => r.OnTime == false).Count()*100)/s.Count()) > 90)? (100 - (s.Where(r => r.OnTime == false).Count()*100)/s.Count()) - 90 : 0,
                    Date = s.Key.Period,
                    Partnership = s.Key.Vendor 
                
            }).OrderBy(s => s.Date).GroupBy(g => g.Partnership).Select(s => new ScoreCard{
                KPI = "OTD",
                CalculationMethod = "(Late Orders *100/Total Orders)",
                Target = 100,
                Frecuency = ReportFrecuency.Monthly,
                FullScore = 10,
                Category = "Delivery",
                Partnership = s.Key,
                Performance = s.ToList(),
                DataSource = "OTDReceipt",
            });
            //return Ok(_context.SaveChanges());
            
            // foreach (var item in groupOTD){ updated+= this.updateScoreCard(item,1);}
            // return Ok(updated);
            
            // // // -- OTD --
            
            // // // -- Spend --
            List<PurchaseReceipts> _receipts = _context.PurchaseReceipts.Where(w =>  w.ReceivedDate >= fecha && w.ReceivedDate < lastdate ).ToList();
           

            // // -- Inflation -- 
            var ReceiptsLast = _context.PurchaseReceipts.Where(w =>  w.ReceivedDate.Year == fecha.AddYears(-1).Year && w.Product != "Unspecified" )
                    .GroupBy(r => new{r.Product,r.SupplierName}).Select(r => new{ Supplier = r.Key.SupplierName, Product = r.Key.Product, Price = r.Average(r => r.ReceivedPrice)}).ToList();

            var Receipts = _receipts.GroupBy(r => new{ r.SupplierName,r.Product,Period = InternoExtensions.GetLastDayOfMonth(r.ReceivedDate)}).Select(r => new{
                        Date = r.Key.Period,
                        Supplier = r.Key.SupplierName,
                        Product = r.Key.Product, 
                        Price = r.Average(r => r.ReceivedPrice),
                        ReceivedAmount = r.Sum(r => r.ReceiptAmount),
                        ReceivedQty = r.Sum(r => r.ReceivedQty),
                        StdCostExt = r.Sum(r => r.StdCostExt),
                        PPV = r.Sum(r => r.ReceiptAmount) - r.Sum(r => r.StdCostExt),
                        Spend = r.Sum(r => r.ReceiptAmount) - (r.Sum(r => r.ReceiptAmount) - r.Sum(r => r.StdCostExt))
                    }).ToList();
            List<InInflation> _infl = new List<InInflation>();
             
            foreach (var item in Receipts)
            {
                InInflation inf = new InInflation();
                inf.Date = item.Date;
                inf.Supplier = item.Supplier;
                inf.Product = item.Product;
                var t1 = ReceiptsLast.FirstOrDefault(p => p.Product == item.Product && p.Supplier == item.Supplier);
                inf.LastPrice = (t1!=null)? t1.Price : item.Price;
                inf.NowPrice = item.Price;
                inf.ReceivedQty = item.ReceivedQty;
                inf.ReceivedAmount = item.ReceivedAmount;
                inf.PPV = item.PPV;
                inf.Spend = item.Spend ;
                
                inf.CostSaving = (inf.Spend != 0)? Decimal.Round( inf.Inflation/inf.Spend,4) : 0;
                _infl.Add(inf);
            }

            
            //         var stream = new MemoryStream();
            //         //Escribimos en el Documento
            //         using(var writeFile = new StreamWriter(stream, leaveOpen: true)) {
            //             var csv = new CsvWriter(writeFile, provider);
            //             //csv.Configuration.RegisterClassMap<GroupReportCSVMap>();            
            //             csv.WriteRecords(_infl);
            //         }
            //         stream.Position = 0; //reset stream
            //         //Regresamos Documento CSV
            // return File(stream, "application/octet-stream", "Inflation.csv");
            
            var groupInflation = _infl.GroupBy(r => new{ r.Supplier, Period = InternoExtensions.GetLastDayOfMonth(r.Date)} ).Select(s => 
            new ScorePerformance { 
                    Performance = s.Sum( r => r.Inflation),
                    Date = s.Key.Period,
                    Partnership = s.Key.Supplier
                
            }).OrderBy(s => s.Date).GroupBy(g => g.Partnership).Select(s => new ScoreCard{
                KPI = "Inflation",
                CalculationMethod = "(Price LastYear - PriceActual)* ReceivedQty",
                Frecuency = ReportFrecuency.Monthly,
                Category = "Cost",
                Partnership = s.Key,
                Performance = s.ToList(),
                DataSource = "PurchaseReceipts"
            });
            
            
            // foreach (var item in groupInflation){ updated+= this.updateScoreCard(item,2); }

            // return Ok(updated);
            
            var groupSpend = Receipts.GroupBy(r => new{ r.Supplier, Period = InternoExtensions.GetLastDayOfMonth(r.Date)} ).Select(s => 
            new ScorePerformance { 
                    Performance = s.Sum( r => r.Spend),
                    Date = s.Key.Period,
                    Partnership = s.Key.Supplier
                
            }).OrderBy(s => s.Date).GroupBy(g => g.Partnership).Select(s => new ScoreCard{
                KPI = "Spend",
                CalculationMethod = "Sum(ReceiptAmount - order.PPV)",
                Frecuency = ReportFrecuency.Monthly,
                Category = "Spend",
                Partnership = s.Key,
                Performance = s.ToList(),
                DataSource = "PurchaseReceipts"
            });
            
            // foreach (var item in groupSpend){ updated+= this.updateScoreCard(item,1); }
            // return Ok(updated);
            // // // -- Spend --

            var listSuppliers = _context.ScoreCards.GroupBy(g => g.Partnership).Select(s => s.Key).ToList();

            foreach (var name in listSuppliers)
            {
                var cost = _context.ScoreCards.Where(s => (s.KPI == "Spend" || s.KPI == "Inflation" || s.KPI == "Cost Saving")  && s.Partnership == name).ToList();
                List<int> ids = cost.Select(s => s.Id).ToList();
        
                var performanceScore = _context.ScorePerformances.Where(s => cost.Contains(s.ScoreCard)).ToList();
                //return Ok(cost.Where(w => w.Partnership == "XIAMEN J BRACE MEDICAL EQUIPMENT CO LTD"));
                foreach (var supplier in cost.GroupBy(w => w.Partnership))
                {
                    
                    ScoreCard scoreInflation = cost.Where( s => s.KPI == "Inflation").First();
                    if(scoreInflation.Performance != null){
                        scoreInflation.Performance = scoreInflation.Performance.OrderBy(p => p.Date).ToList();      
                    }
                    ScoreCard scoreSpend = cost.Where( s => s.KPI == "Spend").First();                    
                    if(scoreSpend.Performance != null){
                        scoreSpend.Performance = scoreSpend.Performance.OrderBy(p => p.Date).ToList();
                    }
                    decimal acuInflation = 0;
                    decimal acuSpend = 0;
                    List<decimal> listInflation = new List<decimal>();
                    List<decimal> listSpend = new List<decimal>();
                    
                    //return Ok(new{Inflation = inf.Performance, spend = spe.Performance, Cost = (inf.Performance/ spe.Performance) *100});
                    var tscore = new ScoreCard{
                        KPI = "Cost Saving",
                        CalculationMethod = "AVG(Inflation / Spend)",
                        Target = -3,
                        FullScore = 30,
                        Frecuency = ReportFrecuency.Monthly,
                        Category = "Cost",
                        Partnership = supplier.Key,
                        DataSource = "PurchaseReceipts",
                        Performance = new List<ScorePerformance>()
                    };
                    var score  = supplier.FirstOrDefault(w => w.KPI == "Cost Saving") ?? tscore;
                    
                    if(scoreInflation.Performance != null && scoreSpend.Performance != null){
                        foreach (var inf in scoreInflation.Performance)
                        {
                            foreach (var spe in scoreSpend.Performance)
                            {
                                if(InternoExtensions.GetLastDayOfMonth(spe.Date) == InternoExtensions.GetLastDayOfMonth(inf.Date))
                                {
                                    listInflation.Add( acuInflation += inf.Performance); 
                                    listSpend.Add(acuSpend += spe.Performance);
                                    //score.Performance = _context.ScorePerformances.Where(p => p.ScoreCard.Id == score.Id).ToList();
                                    var perfor = new ScorePerformance {
                                        Date = spe.Date,
                                        Partnership = inf.Partnership
                                    };
                                    try{
                                        if(acuInflation != 0 && acuSpend != 0){
                                            var temp = score.Performance.FirstOrDefault(p => InternoExtensions.GetLastDayOfMonth(p.Date) == InternoExtensions.GetLastDayOfMonth(spe.Date)) ?? perfor;
                                            temp.Performance = Decimal.Round((acuInflation/acuSpend)*100,1);
                                            temp.Score = Decimal.Parse(this.getCostScore(temp.Performance).ToString()); //Decimal.Parse( this.getCostScore(acuInflation/acuSpend*100).ToString());
                                            
                                            if(temp.Id == 0 ){
                                                score.Performance.Add(temp);
                                            }
                                        }
                                    }catch(System.ArgumentNullException){
                                        return BadRequest(score);
                                    }
                                }
                            }
                        }
                    }
                    
                    _context.ScoreCards.Update(score);
                    updated+= _context.SaveChanges();
                }
            }
            return Ok(updated);
            
            
            // var per = _context.ScorePerformances.Where(s => cost.Contains(s.ScoreCard)).Select(s => new{ s.Date,s.Performance,s.ScoreCard.Partnership,s.ScoreCard.KPI,s}).ToList();
            // return Ok(per);
            
            

            // List<string> suppliers = _context.ScoreCards.GroupBy(g => g.Partnership).Select(s => s.Key).ToList();
            
            // var init = fecha;
            // var con = 1;
            
            
            // while (init < DateTime.Now.Date)
            // {
            //     //Ultima fecha del Mes
            //     var tDate = InternoExtensions.GetLastDayOfMonth(init);
                
            //     foreach (var sup in suppliers)
            //     {
                    
            //         decimal acuInflation = 0;
            //         decimal acuSpend = 0;
                    
            //         var tInflation = per.FirstOrDefault(p => p.Partnership == sup && p.Date == tDate && p.KPI == "Inflation");
            //         var tSpend = per.FirstOrDefault(p => p.Partnership == sup && p.Date == tDate && p.KPI == "Spend");
                    
            //         decimal perValue = 0;
            //         if(tInflation != null && tSpend != null && tInflation.s.Performance != 0 && tSpend.s.Performance !=0){
                        
            //             acuInflation += tInflation.s.Performance;
            //             acuSpend += tSpend.s.Performance;
            //             perValue = (((tInflation.s.Performance/tSpend.s.Performance)/con)*100);
            //             perValue = acuInflation/acuSpend;
            //         }
            //         if(perValue != 0){
            //             var tscore = new ScoreCard{
            //                 KPI = "Cost Saving",
            //                 CalculationMethod = "AVG(Inflation / Spend)",
            //                 Target = -3,
            //                 FullScore = 30,
            //                 Frecuency = ReportFrecuency.Monthly,
            //                 Category = "Cost",
            //                 Partnership = sup,
            //                 DataSource = "PurchaseReceipts",
            //                 Performance = new List<ScorePerformance>()
            //             };


            //             var score  = _context.ScoreCards.FirstOrDefault(w => w.KPI == "Cost Saving" && w.Partnership == sup) ?? tscore;
                        
            //             if(score.Id != 0){
            //                 score.Performance = _context.ScorePerformances.Where(w => w.ScoreCard.Id == score.Id).OrderBy(o => o.Date).ToList();
            //             }

                        
                        
            //             if(score.Performance.Any(p => InternoExtensions.GetLastDayOfMonth(p.Date) == InternoExtensions.GetLastDayOfMonth(tDate) )){
                            
            //                 foreach (var item in score.Performance)
            //                 {
                                
            //                     if(InternoExtensions.GetLastDayOfMonth(item.Date) == InternoExtensions.GetLastDayOfMonth(tDate))
            //                     {        
            //                         item.Performance = Decimal.Round(acuInflation/acuSpend,2)*100;
            //                         item.Score = this.getCostScore(Decimal.Round(acuInflation/acuSpend,2)*100);
                                    
            //                     }
            //                 }
            //             }else{
                            
            //                 var perfor = new ScorePerformance { 
            //                     Performance = Decimal.Round(acuInflation/acuSpend,2)*100 ,
            //                     Score = this.getCostScore(Decimal.Round(acuInflation/acuSpend,2)*100),
            //                     Date = tDate,
            //                     Partnership = sup
            //                 };
            //                 score.Performance.Add(perfor);
                            
            //             }
                        
            //             _context.ScoreCards.Update(score);
            //             updated+= _context.SaveChanges();
            //             Console.WriteLine(updated);
            //         }
            //     }
            //     init = init.AddMonths(1);
            //     Console.WriteLine(init);
            //     con++;
                
            // }
            // return Ok(updated);
            
         
            // //-- Payment Terms --
            // var blanks = _context.BlankPOs.Where( b => b.ReleaseDate >= fecha && b.ReleaseDate.Year == DateTime.Now.Year && b.ReleaseDate.Month < DateTime.Now.Month).ToList().GroupBy(b => new{b.Vendor,Period = InternoExtensions.GetLastDayOfMonth(b.ReleaseDate),b.Terms}).Select(s => new{
            //     Period = s.Key.Period,
            //     Supplier = s.Key.Vendor,
            //     Terms = s.Key.Terms,
            //     Value = this.getPaymentTermsScore(s.Key.Terms),
            //     Pos = s.Count()
            // }).OrderBy(o => o.Value).ToList().GroupBy(g => new{ g.Supplier, g.Period }).Select(s => s.First()).ToList();

            // var ptg = blanks.Select(s => 
            // new ScorePerformance { 
            //         Performance = Decimal.Parse((s.Terms.Substring(s.Terms.Length - 2,2))),
            //         Score = s.Value,
            //         Date = s.Period,
            //         Partnership = s.Supplier
            // }).OrderBy(s => s.Date).GroupBy(g => g.Partnership).Select(s => new ScoreCard{
            //     KPI = "Payment Term",
            //     CalculationMethod = "Min( Day Value Pay Term)",
            //     Target = 5,
            //     Frecuency = ReportFrecuency.Quarterly,
            //     FullScore = 5,
            //     Category = "Business  Terms",
            //     Partnership = s.Key,
            //     Performance = s.ToList(),
            //     DataSource = "BlankPOs",
            // });
            // foreach (var item in ptg){ updated+= this.updateScoreCard(item); }
            //-- Payment Terms --
            return BadRequest(updated);

        }

        [HttpGet("Balance/{filter}")]
        public IActionResult getBalance(string filter)
        {
            switch (filter.ToLower())
            {
                case "rljones": return Ok(_context.BalanceOnHands.ToList());
                default: return BadRequest();
            }
        }


        //Carda de Reportes de Scorecard

        [HttpPost("CalculateScore/Quality")]
        [RequestFormLimits(MultipartBodyLengthLimit = 209715200)]
        [RequestSizeLimit(209715200)]
        public IActionResult setQualityKPI([FromForm] IFormFile file)
        {
            
            if(file.Length > 0)
            {
                
                DataTable Report = ReportController.ExcelToDataTable( file.OpenReadStream())[0];
                Object[] last = Report.Rows[Report.Rows.Count-1].ItemArray;
                //int count =  _context.Database.ExecuteSqlRaw("TRUNCATE TABLE `dbinterno`.`purchasereceipts`;");
                foreach (DataRow row in Report.Rows)
                {
                    return Ok(row);
                }
            }
            return BadRequest();
        }
        public int updateScoreCard(ScoreCard item,int type)
        {
            var scope = _context.ScoreCards.FirstOrDefault(w => w.KPI == item.KPI && w.Partnership == item.Partnership) ?? item;
            
            switch (type)
            {
                case 1:
                    if(scope != null){
                        scope.Performance = _context.ScorePerformances.Where(w => w.ScoreCard.Id == scope.Id).ToList();
                    }else{
                        scope = item;
                    }

                    
                    foreach (var per in item.Performance)
                    {
                        var tper = scope.Performance.FirstOrDefault(w => w.Date == per.Date) ?? per;
                        if(tper != null)
                        {
                            tper.Performance = per.Performance;
                        }
                    }
                    
                    _context.ScoreCards.Update(scope);
                    return _context.SaveChanges();
                case 2:
                    if(scope.Id != 0){
                        scope.Performance = _context.ScorePerformances.Where(w => w.ScoreCard.Id == scope.Id).ToList();
                    }
                    
                    if(item.Performance.Count() > 0){
                        foreach (var per in item.Performance)
                        {
                            var month = scope.Performance.FirstOrDefault(w => InternoExtensions.GetLastDayOfMonth(w.Date) == InternoExtensions.GetLastDayOfMonth(per.Date)) ?? per;
                            if(month.Id == 0){
                                per.ScoreCard = scope;
                                scope.Performance.Add(per);
                            }else{
                                month.Performance = per.Performance;
                                month.Score = per.Score;
                            }
                        }
                    }
                    
                    _context.ScoreCards.Update(scope);
                    return _context.SaveChanges();
                default: return 0;
            }
                


            
            
        }

        private double getCostScore(decimal performance )
        {
            var qty = Double.Parse(performance.ToString());
            
            double score = 30;
            if(qty >= -3){
                for (double i = -3; i < 3; i = i + (0.1))
                {
                    var tval = Math.Round(i,1);
                    //Console.WriteLine(new{qty,tval,i,score});
                    if(qty == tval){
                        return score;
                    }
                    score-= 0.5;
                }
            }else return 30;
            return 0;
            //     switch (val){
            //         case -3: return 30; //X < -2 
            //         case -2: return 25; //X < -1
            //         case -1: return 20; //X < 0
            //         case 0: return 15;//X < 1
            //         case 1: return 10; // X < 2
            //         case 2: // 2 < X(2.2) < 3
            //             double x = Double.Parse(Decimal.Round(performance,1).ToString());
            //             switch (x)
            //             {
            //                 case 2.1: return 4.5;
            //                 case 2.2: return 4;
            //                 case 2.3: return 3.5;
            //                 case 2.4: return 3;
            //                 case 2.5: return 2.5;
            //                 case 2.6: return 2;
            //                 case 2.7: return 1.5;
            //                 case 2.8: return 1;
            //                 case 2.9: return 0.5;
            //             } 
            //             return 5;// 2.0
            //         //break;
            //         default: return 0;// >=3
            //     }
            // }
            // return 30;// <= -3
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

        //Interface para el calculo de Inflacion del ScoreCard
        public class InInflation
        {
            public string Supplier { get; set; }
            public string Product { get; set; }
            public decimal LastPrice { get; set; }
            public decimal NowPrice { get; set; }
            public decimal ReceivedQty { get; set; }
            public decimal ReceivedAmount { get; set; }
            public decimal Inflation { get{ return  Decimal.Round(( NowPrice - LastPrice ) * ReceivedQty,4) ; } }
            public decimal PPV { get; set; }
            public decimal Spend { get; set; }
            public decimal CostSaving { get; set; }
            public DateTime Date {get; set;}
        }
    }
}