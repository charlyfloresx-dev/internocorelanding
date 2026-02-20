using System;
using System.Data;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;
using System.DirectoryServices;
using System.DirectoryServices.Protocols;
using System.DirectoryServices.AccountManagement;

using Microsoft.Extensions.Options;
using Microsoft.EntityFrameworkCore;
using Interno.DJO.Models;
using Interno.DJO.Helpers;
using Interno.DJO.Services;

namespace Interno.DJO.Controllers
{
    [ApiController]
    [Route("[controller]")]
    public class UserController : ControllerBase
    {
        private readonly AppSettings _appSettings;
        private readonly IEmailService _emailService;
        private readonly ILogger<UserController> _logger;
        private readonly DJOContext _context;

        public UserController(ILogger<UserController> logger, IEmailService emailService,IOptions<AppSettings> appSettings, DJOContext context)
        {
            _logger = logger;
            _emailService = emailService;
            _appSettings = appSettings.Value;
            _context = context;
        }

        

        [HttpGet("Roles")]
        public IActionResult getCatalogRoles() => Ok(Enum.GetNames(typeof(InternoRoles)));

        //GET WINDOWS USER
        [HttpGet("User")]
        public IActionResult GetUser() => Ok( HttpContext.User.Identity.Name.Split("\\")[1]);//Usuario de Windows

        [HttpGet("Data")] 
        public IActionResult GetTModel()
        {//Datos de Usuario de Windows
            ResultPropertyCollection data = getUserData();
            if(data != null){ return Ok(data); }
            ModelState.AddModelError("User","Problems to load User Data");
            return BadRequest(ModelState);
        }
        
        [HttpGet("Manager")]
        public IActionResult getManager()
        {
            ResultPropertyCollection data = getUserData();
            
            var user = data["manager"][0].ToString().Split(",")[0].Replace("CN=","");
            
            DirectorySearcher dirSearcher = new DirectorySearcher();
                //Conexion con Active Directory
                DirectoryEntry entry = new DirectoryEntry(dirSearcher.SearchRoot.Path);
                //Filtramos en el Directorio por el Usuario
                dirSearcher.Filter = "(&(objectClass=user)(objectcategory=person)(displayname="+user+"*))";
                dirSearcher.PropertiesToLoad.Add("mail");
                dirSearcher.PropertiesToLoad.Add("usergroup");
                dirSearcher.PropertiesToLoad.Add("displayname");//first name
                dirSearcher.PropertiesToLoad.Add("title");
                dirSearcher.PropertiesToLoad.Add("directreports");
                dirSearcher.PropertiesToLoad.Add("manager");
                SearchResult srEmail = dirSearcher.FindOne();//Seleccionamos el primero registro
                return Ok(srEmail.Properties);//Regresamos las Propiedades del Usuario
        }
        //Send Mail to Windows User
        [HttpGet("Mail")]
        public IActionResult SendMail()
        {//Datos de Usuario de Windows
            //ResultPropertyCollection data = getUserData();
            //if(data != null){
                //Envio de Correo Electronico
                _emailService.Send(_appSettings.EmailFrom, "carlosjavier.flores@enovis.com","Test","Prueba de Correo");
                /*
                var body = new IEmailBody();
                body.Title = "Test Correo Power BI";
                body.Body = "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum.";
                body.Link = "#";
                body.LinkTitle ="Prueba de Link";
                _emailService.SendNotif("Omar.Romo@djoglobal.com","Test Mail BI",body);
                */
                return Ok(true);
            // }
            // ModelState.AddModelError("User","Problems to load User Data");
            //return BadRequest(ModelState);
        }


        [HttpGet("All")]
        public IActionResult getAllusers()
        {
            List<Interno.DJO.Models.Users> lstADUsers = new List<Interno.DJO.Models.Users>();
            DirectorySearcher search = new DirectorySearcher();
            search.Filter = "(&(objectClass=user)(objectCategory=person))";
            search.PropertiesToLoad.Add("samaccountname");
            search.PropertiesToLoad.Add("mail");
            search.PropertiesToLoad.Add("usergroup");
            search.PropertiesToLoad.Add("displayname");//first name
            SearchResult result;
            SearchResultCollection resultCol = search.FindAll();
            if (resultCol != null)
            {
                for (int counter = 0; counter < resultCol.Count; counter++)
                {
                    string UserNameEmailString = string.Empty;
                    result = resultCol[counter];
                    if (result.Properties.Contains("samaccountname") && 
                            result.Properties.Contains("mail") && 
                        result.Properties.Contains("displayname"))
                    {
                        Interno.DJO.Models.Users objSurveyUsers = new Interno.DJO.Models.Users();
                        objSurveyUsers.Email = (String)result.Properties["mail"][0] + 
                        "^" + (String)result.Properties["displayname"][0];
                        objSurveyUsers.UserName = (String)result.Properties["samaccountname"][0];
                        objSurveyUsers.DisplayName = (String)result.Properties["displayname"][0];
                        lstADUsers.Add(objSurveyUsers);
                    }
                }
            }
            return Ok(lstADUsers);
        }

        [HttpGet("Search/{search}")] 
        public IActionResult getAllUser(string search)
        {
            List<Interno.DJO.Models.Users> list = new List<Interno.DJO.Models.Users>();
            //var user = HttpContext.User.Identity.Name.Split("\\")[1];
            DirectorySearcher dirSearcher = new DirectorySearcher();
            DirectoryEntry entry = new DirectoryEntry(dirSearcher.SearchRoot.Path);
            dirSearcher.Filter = "(&(objectClass=user)(objectcategory=person)(displayname=*" + search + "*))";
            var srEmail = dirSearcher.FindAll();
            foreach (var item in srEmail.Cast<SearchResult>().ToList())
            {
                Interno.DJO.Models.Users user = new Interno.DJO.Models.Users();
                user.DisplayName = item.Properties["displayname"][0].ToString();
                try{ user.Email = item.Properties["mail"][0].ToString(); }catch(System.ArgumentOutOfRangeException){ }
                user.UserName = item.Properties["samAccountName"][0].ToString();
                list.Add(user);
            }
            return Ok(list);
        }

        [HttpPost("Role")]
        public IActionResult getUserRole(IClaim claim){
            var user = HttpContext.User.Identity.Name.Split("\\")[1];
            return Ok(_context.Claims.FirstOrDefault(c => c.Claim ==  claim.Claim && c.UserUserName.ToLower() == user.ToLower()));
        } 

        [HttpPost]

        //Windows User Data
        public ResultPropertyCollection getUserData()
        {
            try{
                //var user = Environment.UserName; //Cargamos Usuario de Windows\
                var user = HttpContext.User.Identity.Name.Split("\\")[1];
                
                DirectorySearcher dirSearcher = new DirectorySearcher();
                //Conexion con Active Directory
                DirectoryEntry entry = new DirectoryEntry(dirSearcher.SearchRoot.Path);
                //Filtramos en el Directorio por el Usuario
                dirSearcher.Filter = "(&(objectClass=user)(objectcategory=person)(samAccountName=" + user + "*))";
                SearchResult srEmail = dirSearcher.FindOne();//Seleccionamos el primero registro
                return srEmail.Properties;//Regresamos las Propiedades del Usuario
            }catch(System.NullReferenceException ){
                throw new System.NullReferenceException("Problems to Load User Data or it does not exist.");
            }
        }

        // "data":{"user":{"email":"CarlosJavier.Flores@djoglobal.com","userName":"CarFlores","displayName":"Carlos Javier Flores Montoya","isMapped":false},
        // "internoRole":"Administrator"}
        [HttpPost("Claim")]
        public IActionResult setUserClaim(InternoClaim data)
        {
            if(ModelState.IsValid){
                
                InternoClaim claim = _context.Claims.FirstOrDefault(c => c.Claim ==  data.Claim && c.UserUserName.ToLower() == data.User.UserName.ToLower() ) ?? new InternoClaim();
                
                if(claim.Id != 0){
                    _context.Entry(claim).State = EntityState.Detached;
                    claim.InternoRole = data.InternoRole;

                    _context.Claims.Update(claim);
                }else{
                    claim.User = _context.Users.FirstOrDefault(u => u.UserName == data.User.UserName);
                    if(claim.User != null){
                        claim.UserUserName = data.User.UserName ?? null;
                        claim.InternoRole = data.InternoRole;
                        claim.Claim = data.Claim;
                        _context.Claims.Add(claim);
                    }
                }
                return Ok(_context.SaveChanges());
            }
            return BadRequest(ModelState);
        }


        public ResultPropertyCollection findUser(string user)
        {
            try{
                
                DirectorySearcher dirSearcher = new DirectorySearcher();
                //Conexion con Active Directory
                DirectoryEntry entry = new DirectoryEntry(dirSearcher.SearchRoot.Path);
                //Filtramos en el Directorio por el Usuario
                dirSearcher.Filter = "(&(objectClass=user)(objectcategory=person)(samAccountName=" + user + "*))";
                SearchResult srEmail = dirSearcher.FindOne();//Seleccionamos el primero registro
                return srEmail.Properties;//Regresamos las Propiedades del Usuario
            }catch(System.NullReferenceException ){
                throw new System.NullReferenceException("Problems to Load User Data or it does not exist.");
            }
        }

        
    }
}
