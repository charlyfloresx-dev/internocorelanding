using Microsoft.AspNetCore.Mvc;
using Interno.Inventory;

namespace Interno.PointOfSale.Controllers
{
    public class SaleController : ControllerBase
    {
        public SaleController()
        {

        }

        [HttpGet(Name = "SetSale")]
        public IActionResult SetSale(Interno.Inventory.Models.Document data)
        {
            if(ModelState.IsValid)
            {
                
            }
            return BadRequest();
        }
    }
}