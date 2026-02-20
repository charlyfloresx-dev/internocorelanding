using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Http;
using Interno.Users.Models;
using Interno.Users.Services;

namespace Interno.Users.Controllers
{
    [Authorize]
    [Route("api/[controller]")]
    [ApiController]
    public class UsersController : ControllerBase
    {
        private Interno.Users.Services.IUserServices _userServices;
        public UsersController(IUserServices userServices)
        {
            _userServices = userServices;
        }
        [AllowAnonymous]
        [HttpPost("authenticate")]
        public IActionResult Authenticate([FromBody] AuthenticateRequest model)
        {
            var response = _userServices.Authenticate(model, ipAddress());
            if(response == null) ModelState.AddModelError("Authenticate","User or Password is Incorrect.");
            if(ModelState.IsValid){
                setTokenCookie(response.RefreshToken);
                return Ok(response);
            }else return BadRequest(ModelState);
        }
        [AllowAnonymous]
        [HttpPost("refresh-token")]
        public IActionResult RefreshToken()
        {
            var refreshToken = Request.Cookies["refreshToken"];
            var response = _userServices.RefreshToken(refreshToken, ipAddress());
            if(response == null) return Unauthorized(new { message = "Invalid token" });
            setTokenCookie(response.RefreshToken);
            return Ok(response);
        }
        
        [HttpPost("revoke-token")]
        public IActionResult RevokeToken([FromBody] RevokeTokenRequest model)
        {
            var token = model.Token ?? Request.Cookies["refreshToken"];
            if(string.IsNullOrEmpty(token)) ModelState.AddModelError("Token","Token is Required.");
            var response = _userServices.RevokeToken(token,ipAddress());
            if(!response) ModelState.AddModelError("Token","Token not found.");
            if(ModelState.IsValid){
                return Ok("Token Revoked");
            }else return BadRequest(ModelState);
        }

        [HttpGet("")]
        public IActionResult GetAll() => Ok(_userServices.GetAll());

        [HttpGet("{id}")]
        public IActionResult GetById(int id) => Ok(_userServices.GetById(id));

        [HttpGet("{id}/refresh-tokens")]
        public IActionResult GetRefreshTokens(int id) => Ok(_userServices.GetById(id).RefreshTokens);
        private void setTokenCookie(string token)
        {
            var cookieOptions = new CookieOptions
            {
                HttpOnly = true,
                Expires = DateTime.UtcNow.AddDays(7)
            };
            Response.Cookies.Append("refreshToken",token,cookieOptions);
        }
        private string ipAddress()
        {
            if(Request.Headers.ContainsKey("X-Forwarded-For"))
                return Request.Headers["X-Forwarded-For"];
            else return HttpContext.Connection.RemoteIpAddress.MapToIPv4().ToString();
        }
    }
}