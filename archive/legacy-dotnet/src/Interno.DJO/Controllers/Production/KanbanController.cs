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
using System.Drawing;
using System.Drawing.Printing; 

namespace Interno.DJO.Controllers
{
    [ApiController]
    [Route("[controller]")]
    public class KanbanController : ControllerBase
    {
        private readonly DJOContext _context;
        public KanbanController(Interno.DJO.DJOContext context)
        {
            _context = context;
        }

        [HttpPost("Bin")]
        [RequestFormLimits(MultipartBodyLengthLimit = 209715200)]
        [RequestSizeLimit(209715200)]
        public IActionResult uploadBinInfo([FromForm] IFormFile file)
        {
            if(file.Length > 0){
                DataTable Report = ReportController.CSVtoDataTable( file.OpenReadStream());
                var Bins = _context.Bins.ToList();
                var init = Bins.Max(b => b.Id);
                for (int i = 1; i < Report.Rows.Count; i++)
                {
                    if(!String.IsNullOrEmpty(Report.Rows[i]["qty"].ToString())){
                        var bin =  new Models.Production.Bin();
                        
                        //Interno.DJO.Models.Production.Bin bin = new Interno.DJO.Models.Production.Bin();
                        bin.Item = Report.Rows[i]["item"].ToString();
                        bin.Resource = Report.Rows[i]["resource"].ToString().ToString().Replace("..","");
                        bin.SubResource = Report.Rows[i]["subResource"].ToString().ToString().Replace("..","").Replace("-","");
                        bin.Location = Report.Rows[i]["location"].ToString();
                        bin.Qty = (!String.IsNullOrEmpty(Report.Rows[i]["qty"].ToString()))? Int32.Parse( Report.Rows[i]["qty"].ToString()) : 0;
                        bin.Logo = Report.Rows[i]["logo"].ToString();
                        bin.Hours = (!String.IsNullOrEmpty(Report.Rows[i]["hours"].ToString()))? Int16.Parse( Math.Round(Decimal.Parse(Report.Rows[i]["hours"].ToString())).ToString() ) : 0 ;
                        
                        bin.UOM = Report.Rows[i]["uom"].ToString();
                        bin.PackingType = Report.Rows[i]["packingType"].ToString();
                        bin.BinSize = Report.Rows[i]["binSize"].ToString();
                        bin.Color = Report.Rows[i]["color"].ToString();
                        bin.SubInvetorySource = Report.Rows[i]["subInvetorySource"].ToString().Replace("..","");
                        bin.LocatorSource = Report.Rows[i]["locatorSource"].ToString().Replace("..","");
                        
                        var temp = Bins.Where(b => b.Item == Report.Rows[i]["item"].ToString() 
                                    && b.Resource == Report.Rows[i]["resource"].ToString().ToString().Replace("..","")
                                    && b.SubResource == Report.Rows[i]["subResource"].ToString().ToString().Replace("..","")
                                    && b.Location == Report.Rows[i]["location"].ToString().ToString().Replace("..",""));
                        
                        foreach (var item in temp)
                        {
                            if(item.Qty != bin.Qty || item.Hours != bin.Hours || item.BinSize != bin.BinSize || item.QtyBines != bin.QtyBines 
                            || item.Color != bin.Color || item.SubInvetorySource != bin.SubInvetorySource || item.LocatorSource != bin.LocatorSource){
                                item.Bloqued = true;
                                _context.Bins.Update(item);
                            }
                        }
                        init++;
                        bin.Id= init;
                        _context.Bins.Add(bin);
                    }
                }
                try{
                    return Ok(_context.SaveChanges());
                }catch(Microsoft.EntityFrameworkCore.DbUpdateConcurrencyException){ return BadRequest("No Items Updated");}
                
            }
            return BadRequest();
        }

        [HttpPost("Assorment")]
        public IActionResult setAssortment(Interno.DJO.Models.Production.Assortment data)
        {
            if(data.BinId == 0) ModelState.AddModelError("BinId","Bin Label Number is required.");
            if(data.ConsumedEmp == 0) ModelState.AddModelError("ConsumedEmp","Employee Number is required.");
            if(_context.Bins.Any(b => b.Id == data.BinId && b.Bloqued != true)) ModelState.AddModelError("BinLabel","Label Bin is bloqued, please update info Label.");

            if(ModelState.IsValid){
                if(!_context.Assortments.Any(a => a.ConsumedDate.Date == DateTime.Now.Date && a.AssortmentDate == DateTime.MinValue && a.BinId == data.BinId)){
                    
                    _context.Assortments.Add(data);
                    if(_context.SaveChanges() > 0){
                        return Ok(data);
                    }
                }else{ModelState.AddModelError("Bin","Bin is Sorted or Sorted not completed.");}
            }
            return BadRequest(ModelState);
        }

        [HttpPost("Assorment/Update")]
        public IActionResult updateAssortment(Interno.DJO.Models.Production.Assortment data)
        {
            try{
                if(data != null){
                    if(data.AssortmentDate == DateTime.MinValue && data.AssortmentEmp != 0){
                        data.AssortmentDate = DateTime.Now;
                    }
                    if(data.Completed == DateTime.MinValue && data.CompletedEmp != 0){
                        data.Completed = DateTime.Now;
                    }
                    _context.Assortments.Update(data);
                    if(_context.SaveChanges()>0){ return Ok(data); }
                }
                return BadRequest(ModelState);
            }catch(System.InvalidCastException){ return BadRequest(data);}
            
        }
        
        [HttpGet("Dashboard/{resource}")]
        public IActionResult getDashboardAssortment(string resource) => Ok(_context.Assortments.Include(a => a.Bin)
                                .Where(a=> a.Bin.LocatorSource == resource && (a.Completed.Date == DateTime.Now.Date || a.Completed.Date == DateTime.MinValue)));

        [HttpGet("Bin/Labels")]
        public IActionResult GetItemsLabels(){
            return Ok(_context.Bins.Where(b => b.Bloqued == false).ToList());
        }

        [HttpGet("Bin/Label/{id}")]
        public IActionResult printBinLable(int id){
            var bin = _context.Bins.FirstOrDefault(bn=> bn.Id == id);
            var bom = _context.BOMs.FirstOrDefault(b => b.Component == bin.Item);
            if(bin != null && bom != null) bin.Description = bom.ComponentDescription;
            return Ok(bin);
        }

        [HttpGet("LocalSourceList")]
        public IActionResult getLocalSourceList()
        {
            return Ok(_context.Bins.Where(b=> b.SubInvetorySource == "WIP").GroupBy(b => b.LocatorSource).Select(b => b.Key).ToList());
        }

        [HttpGet("Modules")]
        public IActionResult getModulesList()
        {
            return Ok(_context.Assortments.Include(a => a.Bin).GroupBy(a => a.Bin.Resource).Select(b => b.Key).ToList());
        }

        [HttpGet("Modules/{resource}/Pending")]
        public IActionResult getModulePending(string resource)
        {
            return Ok(_context.Assortments.Include(b => b.Bin).Where(b => b.Bin.Resource == resource && (b.Completed.Date == DateTime.Now.Date || b.Completed.Date == DateTime.MinValue))
                            .OrderBy(a => a.AssortmentDate).ToList());
        }
        
    }
}
