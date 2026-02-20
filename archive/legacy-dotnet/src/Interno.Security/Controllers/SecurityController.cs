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
    public class SecurityController : ControllerBase
    {
        private readonly SecurityContext _context;

        public SecurityController(SecurityContext context)
        {
            _context = context;
        }

        // GET: api/Security
        [HttpGet]
        public async Task<ActionResult<IEnumerable<SecurityGuard>>> GetSecurityGuard()
        {
            return await _context.SecurityGuard.ToListAsync();
        }

        // GET: api/Security/5
        [HttpGet("{id}")]
        public async Task<ActionResult<SecurityGuard>> GetSecurityGuard(int id)
        {
            var securityGuard = await _context.SecurityGuard.FindAsync(id);

            if (securityGuard == null)
            {
                return NotFound();
            }

            return securityGuard;
        }

        // PUT: api/Security/5
        // To protect from overposting attacks, enable the specific properties you want to bind to, for
        // more details, see https://go.microsoft.com/fwlink/?linkid=2123754.
        [HttpPut("{id}")]
        public async Task<IActionResult> PutSecurityGuard(int id, SecurityGuard securityGuard)
        {
            if (id != securityGuard.Id)
            {
                return BadRequest();
            }

            _context.Entry(securityGuard).State = EntityState.Modified;

            try
            {
                await _context.SaveChangesAsync();
            }
            catch (DbUpdateConcurrencyException)
            {
                if (!SecurityGuardExists(id))
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

        // POST: api/Security
        // To protect from overposting attacks, enable the specific properties you want to bind to, for
        // more details, see https://go.microsoft.com/fwlink/?linkid=2123754.
        [HttpPost]
        public async Task<ActionResult<SecurityGuard>> PostSecurityGuard(SecurityGuard securityGuard)
        {
            _context.SecurityGuard.Add(securityGuard);
            await _context.SaveChangesAsync();

            return CreatedAtAction("GetSecurityGuard", new { id = securityGuard.Id }, securityGuard);
        }

        // DELETE: api/Security/5
        [HttpDelete("{id}")]
        public async Task<ActionResult<SecurityGuard>> DeleteSecurityGuard(int id)
        {
            var securityGuard = await _context.SecurityGuard.FindAsync(id);
            if (securityGuard == null)
            {
                return NotFound();
            }

            _context.SecurityGuard.Remove(securityGuard);
            await _context.SaveChangesAsync();

            return securityGuard;
        }

        private bool SecurityGuardExists(int id)
        {
            return _context.SecurityGuard.Any(e => e.Id == id);
        }
    }
}
