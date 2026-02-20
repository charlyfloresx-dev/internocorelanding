using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Interno.Security.Models;

namespace Interno.Security.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class EmployeeLogController : ControllerBase
    {
        private readonly SecurityContext _context;

        public EmployeeLogController(SecurityContext context)
        {
            _context = context;
        }

        // GET: api/EmployeeLog
        [HttpGet]
        public async Task<ActionResult<IEnumerable<EmployeeLog>>> GetEmployeeLog()
        {
            return await _context.EmployeeLog.ToListAsync();
        }

        // GET: api/EmployeeLog/5
        [HttpGet("{id}")]
        public async Task<ActionResult<EmployeeLog>> GetEmployeeLog(int id)
        {
            var employeeLog = await _context.EmployeeLog.FindAsync(id);

            if (employeeLog == null)
            {
                return NotFound();
            }

            return employeeLog;
        }

        // PUT: api/EmployeeLog/5
        // To protect from overposting attacks, enable the specific properties you want to bind to, for
        // more details, see https://go.microsoft.com/fwlink/?linkid=2123754.
        [HttpPut("{id}")]
        public async Task<IActionResult> PutEmployeeLog(int id, EmployeeLog employeeLog)
        {
            if (id != employeeLog.Id)
            {
                return BadRequest();
            }

            _context.Entry(employeeLog).State = EntityState.Modified;

            try
            {
                await _context.SaveChangesAsync();
            }
            catch (DbUpdateConcurrencyException)
            {
                if (!EmployeeLogExists(id))
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

        // POST: api/EmployeeLog
        // To protect from overposting attacks, enable the specific properties you want to bind to, for
        // more details, see https://go.microsoft.com/fwlink/?linkid=2123754.
        [HttpPost]
        public async Task<ActionResult<EmployeeLog>> PostEmployeeLog(EmployeeLog employeeLog)
        {
            _context.EmployeeLog.Add(employeeLog);
            await _context.SaveChangesAsync();
            return CreatedAtAction("GetEmployeeLog", new { id = employeeLog.Id }, employeeLog);
        }

        // DELETE: api/EmployeeLog/5
        [HttpDelete("{id}")]
        public async Task<ActionResult<EmployeeLog>> DeleteEmployeeLog(int id)
        {
            var employeeLog = await _context.EmployeeLog.FindAsync(id);
            if (employeeLog == null)
            {
                return NotFound();
            }
            _context.EmployeeLog.Remove(employeeLog);
            await _context.SaveChangesAsync();
            return employeeLog;
        }

        private bool EmployeeLogExists(int id)
        {
            return _context.EmployeeLog.Any(e => e.Id == id);
        }
    }
}
