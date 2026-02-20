
using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.AspNetCore.Mvc;

using System.Data;
using Microsoft.AspNetCore.Http;

namespace Interno.DJO.Controllers
{
    [ApiController]
    [Route("[controller]")]
    public class CatalogController : ControllerBase
    {
        private readonly DJOContext _context;

        public CatalogController(DJOContext context)
        {
            _context = context;
        }
        
        [HttpGet]
        public IActionResult getCatalog(){
            return Ok(new {
                Status = Enum.GetNames(typeof(Interno.DJO.Models.StatusType)),
                IssueTypes = Enum.GetNames(typeof(Interno.Production.Models.IssueType)),
                Issues = _context.Issues.OrderBy(i => i.Id).ToList(),
                PriorityLevel = Enum.GetNames(typeof(Interno.Domain.Enum.PriorirtyLevel)),
            });
        } 
    }
}
