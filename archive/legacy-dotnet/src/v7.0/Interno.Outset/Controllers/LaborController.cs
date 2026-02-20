using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Interno.Outset.Models;
using Interno.Production.Models;

namespace Interno.Outset.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class LaborController : ControllerBase
    {
        private readonly OutsetContext _context;

        public LaborController(OutsetContext context)
        {
            _context = context;
        }

        // GET: api/Labor
        [HttpGet]
        public async Task<ActionResult<IEnumerable<Labor>>> GetLabor()
        {
          if (_context.Labor == null)
          {
              return NotFound();
          }
            return await _context.Labor.ToListAsync();
        }

        // GET: api/Labor/5
        [HttpGet("{id}")]
        public async Task<ActionResult<Labor>> GetLabor(int id)
        {
          if (_context.Labor == null)
          {
              return NotFound();
          }
            var labor = await _context.Labor.FindAsync(id);

            if (labor == null)
            {
                return NotFound();
            }

            return labor;
        }

        // PUT: api/Labor/5
        // To protect from overposting attacks, see https://go.microsoft.com/fwlink/?linkid=2123754
        [HttpPut("{id}")]
        public async Task<IActionResult> PutLabor(int id, Labor labor)
        {
            if (id != labor.Id)
            {
                return BadRequest();
            }

            _context.Entry(labor).State = EntityState.Modified;

            try
            {
                await _context.SaveChangesAsync();
            }
            catch (DbUpdateConcurrencyException)
            {
                if (!LaborExists(id))
                {
                    return NotFound();
                }
                else
                {
                    throw;
                }
            }

            return NoContent();
        }

        // POST: api/Labor
        // To protect from overposting attacks, see https://go.microsoft.com/fwlink/?linkid=2123754
        [HttpPost]
        public async Task<ActionResult<Labor>> PostLabor(Labor labor)
        {
          if (_context.Labor == null)
          {
              return Problem("Entity set 'OutsetContext.Labor'  is null.");
          }
            _context.Labor.Add(labor);
            await _context.SaveChangesAsync();

            return CreatedAtAction("GetLabor", new { id = labor.Id }, labor);
        }

        // DELETE: api/Labor/5
        [HttpDelete("{id}")]
        public async Task<IActionResult> DeleteLabor(int id)
        {
            if (_context.Labor == null)
            {
                return NotFound();
            }
            var labor = await _context.Labor.FindAsync(id);
            if (labor == null)
            {
                return NotFound();
            }

            _context.Labor.Remove(labor);
            await _context.SaveChangesAsync();

            return NoContent();
        }

        private bool LaborExists(int id)
        {
            return (_context.Labor?.Any(e => e.Id == id)).GetValueOrDefault();
        }
    }
}
