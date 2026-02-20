
using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.AspNetCore.Mvc;

using System.Data;
using Microsoft.AspNetCore.Http;

namespace Interno.DJO.Controllers
{
    [ApiController]
    [Route("[controller]")]
    public class WHSController : ControllerBase
    {
        private readonly DJOContext _context;

        public WHSController(DJOContext context) { _context = context; } //Instanciamos la Base de Datos al Crear el Controlador

        //Funcion que regresa todas las WorkOrders que no esten Cerradas
        public IActionResult getMoveOrder()
        {
            List<Interno.Production.Models.Resource> _whs = _context.Resources.ToList();
            return Ok(_context.MoveOrders.Where(mo => (mo.Status != Domain.Enum.StatusType.Closed && mo.Status != Domain.Enum.StatusType.Canceled) ).ToList());
        }

        [HttpPost("MoveOrder")]
        public IActionResult updateMoveOrder(Models.MoveOrder data)
        {
            if(data.AssortmentUser == 0 && data.Status != Domain.Enum.StatusType.StandBy){ ModelState.AddModelError("AssortmentUser","User is required to Update Assortmend Status");}

            if(ModelState.IsValid){
                if(data.Status == Domain.Enum.StatusType.InProgress){ data.AssortmenStart = DateTime.Now; }
                _context.MoveOrders.Update(data);
                return Ok(_context.SaveChanges());
            }
            return BadRequest(ModelState);
        }
    }
}