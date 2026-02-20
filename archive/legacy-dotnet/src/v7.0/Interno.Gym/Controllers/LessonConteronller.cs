using System.Data;
using Interno.Domain.Catalog;
using Interno.Gym;
using Interno.Gym.Models;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore.Metadata.Internal;
using Microsoft.SqlServer.Server;

namespace Interno.Outset.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class LessonController : ControllerBase
    {
        private readonly Interno.Gym.Models.GymContext _context;

        public LessonController(GymContext context)
        {
            _context = context;
        }

        // GET: api/Labor
        [HttpGet]
        public IActionResult GetLessons()
        {
            if (_context.Lessons == null)
            {
                return NotFound();
            }
            return Ok(_context.Lessons.ToList());
        }

        [HttpPost]
        public IActionResult SetLesson(Lesson data)
        {
            if (_context.Lessons.Any(r => r.Name.ToUpper() == data.Name.ToUpper())) { ModelState.AddModelError("Name", "That name of the Lesson has already has been registered."); }

            if (ModelState.IsValid)
            {
                _context.Lessons.Add(data);
                return Ok(_context.SaveChanges());
            }
            return BadRequest(ModelState);
        }

        [HttpPost("Tutor")]
        public IActionResult SetLessonTutor(Tutor data)
        {
            if (data.SSN == null && data.RFC == null) { ModelState.AddModelError("Partner.UniqueData", "Unique data is required (SSN,RFC)."); }

            if (ModelState.IsValid)
            {
                return Ok(data);
            }
            return BadRequest(ModelState);
        }
    }
}