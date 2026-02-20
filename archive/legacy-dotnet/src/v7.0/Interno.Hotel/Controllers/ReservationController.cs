using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace Interno.Hotel.Controller
{
    [Route("api/[controller]")]
    [ApiController]
    public class ReceptionController : ControllerBase
    {
        //private readonly OutsetContext _context;

        public ReceptionController()//OutsetContext context)
        {
            //_context = context;
        }

        [HttpGet]
        public IActionResult getReservation()
        {
            return Ok(new Interno.Hotel.Models.Reservation());
        }
    }
}