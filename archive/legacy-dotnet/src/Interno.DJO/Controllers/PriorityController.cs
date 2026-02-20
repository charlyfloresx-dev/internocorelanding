using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;
using Interno.DJO.Models;

namespace Interno.DJO.Controllers
{
    [ApiController]
    [Route("[controller]")]
    public class PriorityController : ControllerBase
    {
        private readonly Interno.DJO.DJOContext _context;
        public PriorityController(DJOContext context)
        {
            _context = context;
        }

        [HttpGet]
        public IActionResult GetPriorities()
        {
            return BadRequest();
        }
        [HttpGet("Claims")]
        public IActionResult getPriorityClaims() => Ok(_context.Claims.Where(c => c.Claim.Contains("priority")).GroupBy(c => c.Claim).Select(r => r.Key).ToArray());

        [HttpPost]
        public IActionResult setPriorityUpdate(Interno.DJO.Models.DJOLog data)
        {
            data.User = HttpContext.User.Identity.Name.Split("\\")[1];
            data.Date = DateTime.Now;
            _context.AddOrUpdate(data);
            return Ok(_context.SaveChanges());
        }
        
        [HttpPost("Available")]
        public IActionResult setAvailability(Interno.DJO.Models.IncomingPriority data)
        {
            if(data.Available == true){
                data.AvailableDate = DateTime.Now;
                //data.UpdatedUser = HttpContext.User.Identity.Name.Split("\\")[1];
                _context.IncomingPriorities.Update(data);
                return Ok(_context.SaveChanges());
            }
            return BadRequest();
        }
    }
}
