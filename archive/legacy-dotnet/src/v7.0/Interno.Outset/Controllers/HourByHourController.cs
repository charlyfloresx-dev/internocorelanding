using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Interno.Outset.Models;
using Interno.Outset.Models.Temp;

namespace Interno.Outset.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class HourByHourController : ControllerBase
    {
        private readonly OutsetContext _context;
        private readonly Interno.Outset.Models.Temp.TulipContext _tulip;

        public HourByHourController(OutsetContext context, TulipContext tulip)
        {
            _context = context;
            _tulip = tulip;
        }

        [HttpGet]
        public IActionResult getHourByHour()
        {
            List<Interno.Outset.Models.Temp.ProductionOutput> _output = _tulip.ProductionOutputs.Where(h => h.End >= DateTime.Now.Date.AddHours(0)).OrderBy(h => h.End).ToList();

            var group = _output.GroupBy(h => new { h.Area, h.Line, h.Station }).Select(h => new
            {
                Station = h.Key.Station,
                Pieces = h.Count(),
                Eficiency = h.Average(h => h.Eficiency) * 100,
                HourByHour = h.GroupBy(h => h.Hora).Select(h => new
                {
                    Hour = h.Key,
                    Pieces = h.Count(),
                    Eficiency = h.Average(h => h.Eficiency) * 100
                }),
                output = h
            });
            return Ok(group);
        }



        // GET: api/HourByHour/5
        [HttpGet("{id}")]
        public async Task<ActionResult<HrxHr>> GetHrxHr(int id)
        {
            if (_context.HourByHour == null)
            {
                return NotFound();
            }
            var hrxHr = await _context.HourByHour.FindAsync(id);

            if (hrxHr == null)
            {
                return NotFound();
            }

            return Ok(hrxHr);
        }

        // PUT: api/HourByHour/5
        // To protect from overposting attacks, see https://go.microsoft.com/fwlink/?linkid=2123754
        [HttpPut("{id}")]
        public async Task<IActionResult> PutHrxHr(int id, HrxHr hrxHr)
        {
            if (id != hrxHr.Id)
            {
                return BadRequest();
            }

            _context.Entry(hrxHr).State = EntityState.Modified;

            try
            {
                await _context.SaveChangesAsync();
            }
            catch (DbUpdateConcurrencyException)
            {
                if (!HrxHrExists(id))
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

        // POST: api/HourByHour
        // To protect from overposting attacks, see https://go.microsoft.com/fwlink/?linkid=2123754
        [HttpPost]
        public IActionResult PostHrxHr(HrxHr data)
        {
            if (ModelState.IsValid)
            {
                var time = _context.OperationTime.FirstOrDefault(op => op.Product == data.Item && op.WarehouseCode == data.ResourceCode);
                if (time != null)
                {
                    data.StdTime = (time.RunTime + time.SetTime).TotalHours;
                    data.EmployeesQty = 1;
                    data.Pieces = data.Pieces;
                    data.PaidHrs = data.StdTime * data.EmployeesQty;

                    var res = this.getResult(data.ResourceCode);
                    if (res != null && res.Id != 0)
                    {
                        data.Result = res;
                    }
                    _context.Add(data);
                }

                _context.SaveChanges();
                return Ok(data);
            }
            return BadRequest(ModelState);
        }

        // DELETE: api/HourByHour/5
        [HttpDelete("{id}")]
        public async Task<IActionResult> DeleteHrxHr(int id)
        {
            if (_context.HourByHour == null)
            {
                return NotFound();
            }
            var hrxHr = await _context.HourByHour.FindAsync(id);
            if (hrxHr == null)
            {
                return NotFound();
            }

            _context.HourByHour.Remove(hrxHr);
            await _context.SaveChangesAsync();

            return NoContent();
        }

        private Interno.Production.Models.Result getResult(string resource)
        {
            Console.Write(resource);
            var result = _context.Result.FirstOrDefault(r => r.Date.Date == DateTime.Now.Date && r.ResourceCode == resource) ?? new Production.Models.Result();
            if (result.Id == 0)
            {
                result.Date = DateTime.Today.AddHours(7);
                result.ResourceCode = resource;
            }
            return result;
        }

        private bool HrxHrExists(int id)
        {
            return (_context.HourByHour?.Any(e => e.Id == id)).GetValueOrDefault();
        }
    }
}
