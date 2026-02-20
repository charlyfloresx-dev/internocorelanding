using System;
using System.Linq;
using Microsoft.AspNetCore.Mvc;
using Interno.Domain.Enum;

using Interno.Production.Models;

namespace Interno.Production.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class CatalogController : ControllerBase
    {
        private readonly ProductionContext _production;
        public CatalogController(ProductionContext production)
        {
            _production = production;
        }
        [HttpGet("")]
        public IActionResult getCatalog()
        {
            var shift = _production.Shift.OrderBy(s => s.Id).Take(2).ToList();
            foreach (var item in shift){
                item.AvailableTime = item.TotalTimeWorkday- item.TotalTimeBreaks;
            }
            var items = _production.OperationTime.ToList();
            foreach (var item in items) item.Hours = item.SetTime.TotalHours;
            var restype = _production.WarehouseType.ToList();
            var res = _production.Resource.ToList();
            foreach (var item in res) item.Type = restype.FirstOrDefault(r => r.Id == item.TypeId);
            var breaks = _production.Break.ToList();
            

            return Ok(new {
                Status = Enum.GetNames(typeof(StatusType)),
                UM = _production.UM.ToList(),
                Resource = res,
                Shift = shift,
                Break = breaks,
                Items = items
            });   
        }
        

        [HttpGet("Status")]
        public IActionResult GetStatus() => Ok();

        
        [HttpGet("UM")]
        public IActionResult GetUM() => Ok(_production.UM.ToList());

        [HttpPost("UM")]
        public IActionResult SetUM([FromBody] Interno.Domain.Catalog.UM data) {
            if(ModelState.IsValid){
                _production.UM.Add(data);
                return Ok(_production.SaveChanges());
            }
            return BadRequest(ModelState);
        }

        [HttpGet("Company")]
        public IActionResult GetCompanies() => Ok(_production.Company.ToList());

        [HttpPost("Company")]
        public IActionResult SetCompany([FromBody] Interno.Domain.Catalog.Company data) {
            if(ModelState.IsValid){
                _production.Company.Add(data);
                return Ok(_production.SaveChanges());
            }
            return BadRequest(ModelState);
        }

        [HttpGet("Resource")]
        public IActionResult GetResources() => Ok(_production.Resource.ToList());

        [HttpPost("Resource")]
        public IActionResult SetResource(Interno.Production.Models.Resource data)
        {
            if(_production.Resource.Any(r => r.Code == data.Code)) ModelState.AddModelError("Code","Resource Code already exists.");
            if(ModelState.IsValid){
                data.TypeId = 1;
                _production.Resource.Add(data);
                return Ok(_production.SaveChanges());
            } return BadRequest(ModelState);
        }
        
        [HttpGet("Break")]
        public IActionResult getBreaks() => Ok(_production.Break.ToList());

        [HttpGet("Shift")]
        public IActionResult getShift()
        { 
            var shift = _production.Shift.OrderBy(s => s.Id).Take(2).ToList();
            foreach (var item in shift) item.AvailableTime = item.End - item.Start;
            return Ok(shift);
        }

        [HttpPost("Shift")]
        public IActionResult setShift(Interno.HumanResource.Models.Catalog.Shift shift)
        {
            if(shift.Start == TimeSpan.Zero) ModelState.AddModelError("Start","Start Time is required.");
            if(shift.End == TimeSpan.Zero) ModelState.AddModelError("End","End Time is required.");
            if(_production.Shift.Any(s => s.Code == shift.Code)) ModelState.AddModelError("Shift","Shift Code already exists.");
            if(ModelState.IsValid){
                shift.AvailableTime = shift.End - shift.Start;
                _production.Shift.Add(shift);
                return Ok(_production.SaveChanges());
            }return BadRequest(ModelState);
        }
    }
}