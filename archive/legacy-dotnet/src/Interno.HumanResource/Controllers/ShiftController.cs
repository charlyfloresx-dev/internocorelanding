using System.Linq;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Interno.HumanResource.Models;

namespace Interno.HumanResource.Controllers
{
    [Route("[controller]")]
    [ApiController]
    public class ShiftController : ControllerBase
    {
        private readonly HRContext _context;
        public ShiftController(HRContext context)
        {
            _context = context;
        }

        [HttpGet]
        public IActionResult getShifts() => Ok(_context.Shift.ToList());

        [HttpGet("GroupBrakes")]
        public IActionResult getShiftGroupBrakes() => Ok(_context.ShifGroupBrakes.Include(s => s.Shift).Include(s => s.BreakGroup).Include(s => s.Break).ToList());

        [HttpGet("Breaks")]
        public IActionResult getBrakes() => Ok(_context.Break.ToList());

        [HttpGet("BreakGroup/{shift}/{group}")]
        public IActionResult getBreakGroup(int shift, int group) => Ok(_context.ShifGroupBrakes.Include(s => s.Break).Where(s => s.BreakGroupId == group && s.ShiftId == shift));
        [HttpPost("GroupBrakes")]
        public IActionResult setBreakGroup(Interno.HumanResource.Models.Catalog.ShifGroupBrakes data)
        {
            if (data.ShiftId == 0)
            {
                if (data.Shift != null && data.Shift.Id != 0) data.ShiftId = data.Shift.Id;
                else ModelState.AddModelError("ShiftId", "Shift is required.");
            }
            if (ModelState.IsValid)
            {
                _context.ShifGroupBrakes.Add(data);
                return Ok(_context.SaveChanges());
            }
            return BadRequest(ModelState);
        }

    }
}

