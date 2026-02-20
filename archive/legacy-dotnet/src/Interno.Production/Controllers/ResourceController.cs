using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Interno.Production.Models;

namespace Interno.Production.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class ResourceController : ControllerBase
    {
        private readonly ProductionContext _context;

        public ResourceController(ProductionContext context)
        {
            _context = context;
        }

        // GET: api/Resource
        [HttpGet]
        public IActionResult GetResource()
        {
            return  Ok(_context.Resource.Include(r => r.Type).ToList());
        }

        // GET: api/Resource/5
        [HttpGet("{id}")]
        public IActionResult GetResource(string id)
        {
            return Ok(GetResourceInfo(id));
        }

        // PUT: api/Resource/5
        // To protect from overposting attacks, enable the specific properties you want to bind to, for
        // more details, see https://go.microsoft.com/fwlink/?linkid=2123754.
        [HttpPut("{id}")]
        public async Task<IActionResult> PutResource(string id, Resource resource)
        {
            if (id != resource.Code)
            {
                return BadRequest();
            }

            _context.Entry(resource).State = EntityState.Modified;

            try
            {
                await _context.SaveChangesAsync();
            }
            catch (DbUpdateConcurrencyException)
            {
                if (!ResourceExists(id))
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

        // POST: api/Resource
        // To protect from overposting attacks, enable the specific properties you want to bind to, for
        // more details, see https://go.microsoft.com/fwlink/?linkid=2123754.
        [HttpPost]
        public async Task<ActionResult<Resource>> PostResource(Resource resource)
        {
            if(resource.TypeId == 0) ModelState.AddModelError("TypeId", "The Type Id is Required.");
            if(ModelState.IsValid){
                _context.Resource.Add(resource);
                await _context.SaveChangesAsync();

                return CreatedAtAction("GetResource", new { id = resource.Code }, resource);
            }
            return BadRequest(ModelState);
        }

        // DELETE: api/Resource/5
        [HttpDelete("{id}")]
        public async Task<ActionResult<Resource>> DeleteResource(int id)
        {
            var resource = await _context.Resource.FindAsync(id);
            if (resource == null)
            {
                return NotFound();
            }

            _context.Resource.Remove(resource);
            await _context.SaveChangesAsync();

            return resource;
        }

        private bool ResourceExists(string id)
        {
            return _context.Resource.Any(e => e.Code == id);
        
        }
        
        protected Resource GetResourceInfo(string search)
        {
            return _context.Resource.FirstOrDefault(r => r.Code == search);
        }
    }
}
