using System.Data;
using Interno.Domain.Catalog;
using Interno.Gym;
using Interno.Gym.Models;
using Interno.HumanResource.Models;
using Interno.Inventory;
using Microsoft.AspNetCore.Mvc;
using Microsoft.DotNet.Scaffolding.Shared.Messaging;
using Microsoft.EntityFrameworkCore;

namespace Interno.Outset.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class SubscriptionController : ControllerBase
    {
        private readonly Interno.Gym.Models.GymContext _context;

        public SubscriptionController(GymContext context)
        {
            _context = context;
        }

        // GET: api/Labor
        [HttpGet]
        public IActionResult GetSubscriptions()
        {
            if (_context.Subscriptions == null)
            {
                return NotFound();
            }
            return Ok(_context.Subscriptions.ToList());
        }

        [HttpGet("Types")]
        public IActionResult getSubscriptionTypes() => Ok(Enum.GetNames(typeof(Interno.Gym.SubscriptionType)));

        [HttpPost]
        public IActionResult createSubscription(Subscription data)
        {
            if (data.Partner.SSN == null && data.Partner.CURP == null && data.Partner.RFC == null) { ModelState.AddModelError("Partner.UniqueData", "Unique data is required (SSN,CURP,RFC)."); }

            Partner exist = _context.Partners.FirstOrDefault(r => r.SSN == data.Partner.SSN || r.CURP == data.Partner.CURP || r.RFC == data.Partner.RFC) ?? new Partner();

            if (exist.Id > 0) { data.Partner = exist; data.PartnerId = exist.Id; }
            if (ModelState.IsValid)
            {
                data.End = data.Start.AddTicks(Subscription.getTicks((SubscriptionType)data.Type)).AddDays(1).Date;
                //Revisar subscripciones del usuario
                List<Subscription> last = _context.Subscriptions.Where(r => r.PartnerId == data.PartnerId && r.End >= data.End).OrderByDescending(r => r.End).ToList();
                if (last.Count > 0)//Tiene subscripcines Activas
                {
                    ModelState.AddModelError("Subscription", "The person has an active subscription.");
                    return Conflict(new { ModelState["Subscription"].Errors, Subscription = last });
                }
                else
                {//Agregamos Subscripcion
                    _context.AddOrUpdate(data);
                    if (_context.SaveChanges() > 0)
                    {
                        return Ok(data);
                    }
                }
            }
            return BadRequest(ModelState);
        }

        [HttpPost("Partner")]
        public IActionResult setPartner(Partner person)
        {
            //Validar la Persona para agregarle
            if (ModelState.IsValid)
            {
                _context.Partners.Add(person);
                if (_context.SaveChanges() > 0)
                {
                    return Ok(person);
                }
                return BadRequest(person);
            }
            return BadRequest(ModelState);
        }

        // // GET: api/Labor/5
        // [HttpGet("{id}")]
        // public async Task<ActionResult<Labor>> GetLabor(int id)
        // {
        //     if (_context.Labor == null)
        //     {
        //         return NotFound();
        //     }
        //     var labor = await _context.Labor.FindAsync(id);

        //     if (labor == null)
        //     {
        //         return NotFound();
        //     }

        //     return labor;
        // }

        // // PUT: api/Labor/5
        // // To protect from overposting attacks, see https://go.microsoft.com/fwlink/?linkid=2123754
        // [HttpPut("{id}")]
        // public async Task<IActionResult> PutLabor(int id, Labor labor)
        // {
        //     if (id != labor.Id)
        //     {
        //         return BadRequest();
        //     }

        //     _context.Entry(labor).State = EntityState.Modified;

        //     try
        //     {
        //         await _context.SaveChangesAsync();
        //     }
        //     catch (DbUpdateConcurrencyException)
        //     {
        //         if (!LaborExists(id))
        //         {
        //             return NotFound();
        //         }
        //         else
        //         {
        //             throw;
        //         }
        //     }

        //     return NoContent();
        // }

        // // POST: api/Labor
        // // To protect from overposting attacks, see https://go.microsoft.com/fwlink/?linkid=2123754
        // [HttpPost]
        // public async Task<ActionResult<Labor>> PostLabor(Labor labor)
        // {
        //     if (_context.Labor == null)
        //     {
        //         return Problem("Entity set 'OutsetContext.Labor'  is null.");
        //     }
        //     _context.Labor.Add(labor);
        //     await _context.SaveChangesAsync();

        //     return CreatedAtAction("GetLabor", new { id = labor.Id }, labor);
        // }

        // // DELETE: api/Labor/5
        // [HttpDelete("{id}")]
        // public async Task<IActionResult> DeleteLabor(int id)
        // {
        //     if (_context.Labor == null)
        //     {
        //         return NotFound();
        //     }
        //     var labor = await _context.Labor.FindAsync(id);
        //     if (labor == null)
        //     {
        //         return NotFound();
        //     }

        //     _context.Labor.Remove(labor);
        //     await _context.SaveChangesAsync();

        //     return NoContent();
        // }

        // private bool LaborExists(int id)
        // {
        //     return (_context.Labor?.Any(e => e.Id == id)).GetValueOrDefault();
        // }
    }
}