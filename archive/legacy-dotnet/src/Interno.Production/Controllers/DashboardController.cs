using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;

using Interno.Production.Models;

namespace Interno.Production.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class DashboardController : ControllerBase
    {
        private readonly ProductionContext _production;
        public DashboardController(ProductionContext context)
        {
            _production = context;
        }

        [HttpGet("Production")]
        public IActionResult GetProductionDashboard()
        {
            List<Result> results = _production.Results.Where(r => r.Date.Date == DateTime.Now.Date).ToList();
            return Ok(results);
        }
    }
}