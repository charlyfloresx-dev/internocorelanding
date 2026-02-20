using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;

using System.IO;
using System.Data;
using System.Text.RegularExpressions;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using ExcelDataReader;

using Interno.HumanResource.Models;
using Interno.Domain;
using Interno.Domain.Catalog;


namespace Interno.HumanResource.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class EmployeeController : ControllerBase
    {
        private readonly HRContext _context;

        public EmployeeController(HRContext context)
        {
            _context = context;
        }

        // GET: api/Employee
        [HttpGet]
        public async Task<ActionResult<IEnumerable<Employee>>> GetEmployees()
        {
            return await _context.Employee.ToListAsync();
        }

        // GET: api/Employee/5
        [HttpGet("{number}")]
        public IActionResult GetEmployeeByNumber(string number) {
            var id = Int32.Parse(Regex.Match(number,@"\d+").Value);
            Interno.HumanResource.Models.Employee employee = _context.Employee.Where( emp => emp.Number == id)
                    .Include(emp => emp.Person).Include(emp => emp.Position).Include(emp => emp.Shift)
                    .Include(emp => emp.BusinessUnit).First();
            return Ok(employee);
        }
        
        [HttpGet("Search/{search}")]
        public IActionResult GetEmployee(string search)
        {
            return Ok(_context.Employee.Where(em => em.Person.PrettyName.Contains(search) )
                            .Include(em => em.Person)
                            .Include(em => em.Position)
                            .Include(em => em.Shift)
                            .ToList());
        }

        // PUT: api/Employee/5
        // To protect from overposting attacks, enable the specific properties you want to bind to, for
        // more details, see https://go.microsoft.com/fwlink/?linkid=2123754.
        [HttpPut("{id}")]
        public async Task<IActionResult> PutEmployee(Guid id, Employee employee)
        {
            if (id != employee.Id)
            {
                return BadRequest();
            }
            _context.Entry(employee).State = EntityState.Modified;

            try
            {
                await _context.SaveChangesAsync();
            }
            catch (DbUpdateConcurrencyException)
            {
                if (!EmployeeExists(id))
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

        // POST: api/Employee
        // To protect from overposting attacks, enable the specific properties you want to bind to, for
        // more details, see https://go.microsoft.com/fwlink/?linkid=2123754.
        [HttpPost]
        public async Task<ActionResult<Employee>> PostEmployee(Employee employee)
        {
            _context.Employee.Add(employee);
            await _context.SaveChangesAsync();

            return CreatedAtAction("GetEmployee", new { id = employee.Id }, employee);
        }

        [HttpPost("Update")]
        public IActionResult UpdateEmployees([FromForm] IFormFile file){
            //Si contiene archivos 
            if(file.Length > 0){
                // Direccion Temporal
                var filePath = Path.GetTempFileName();
                // Datos del Documento
                FileInfo fileInfo = new FileInfo(filePath);
                // Asignamos Atributos a los temporales
                fileInfo.Attributes = FileAttributes.Temporary;
                
                //using (var stream = File.Open(filePath, FileMode.Open, FileAccess.Read))
                //{
                    // Auto-detect format, supports:
                    //  - Binary Excel files (2.0-2003 format; *.xls)
                    //  - OpenXml Excel files (2007 format; *.xlsx)
                    
                int updated = 0;
                
                //Lector de Documentos de Excel
                using (var reader = ExcelReaderFactory.CreateReader(file.OpenReadStream()))
                {
                    //Creamos el DataTable con los registros
                    var result = reader.AsDataSet(new ExcelDataSetConfiguration()
                    {
                        UseColumnDataType = false,
                        ConfigureDataTable = (tableReader) => new ExcelDataTableConfiguration()
                        {
                            UseHeaderRow = true
                        }
                    });
                    
                    DataTable dt = result.Tables[0];
                    _context.Database.ExecuteSqlRawAsync("UPDATE `dbinterno`.`employee` SET `active` = 0;");
                    //Recorremos los Registros                     
                    foreach (DataRow row in dt.Rows) {
                        char[] charTotrim = {' '};
                        Employee employee = new Employee();
                        employee.Number = Int32.Parse(row[0].ToString());
                        string[] Nombre = row[1].ToString().Split(',');
                        Nombre[1] = Nombre[1].Trim(charTotrim);
                        string[] Apellidos = Nombre[0].Split(' ');
                        string[] Nombres = Nombre[1].Split(' ');
                        Interno.Domain.Catalog.Person person = new Interno.Domain.Catalog.Person();
                        person.LastNamePat = Apellidos[0];
                        if(Apellidos[1] != null){
                            person.LastNameMat = Apellidos[1];
                        }
                        person.FirstName = Nombres[0].Trim(charTotrim);
                        if(Nombres.Count() == 2){
                            person.MiddleName = Nombres[1].Trim(charTotrim);
                        }
                        person.PrettyName = row[1].ToString();
                        
                        var findPerson = _context.Person.FirstOrDefault(per => per.LastNamePat == person.LastNamePat && per.LastNameMat == person.LastNameMat && per.FirstName == person.FirstName);

                        if(findPerson != null){ person = findPerson; }
                        employee.Person = person;
                        employee.Active = true;
                        employee.Shift = _context.Shift.FirstOrDefault(po => po.Name == row[4].ToString());
                        if(employee.Shift == null){ 
                            employee.Shift = new Models.Catalog.Shift();
                            employee.Shift.Code = _context.Shift.Count().ToString();
                            employee.Shift.Name =  row[4].ToString();
                        }
                        /*
                        employee.BusinessUnit = _context.BusinessUnits.FirstOrDefault(bu => bu.Name == row[4].ToString());
                        if(employee.BusinessUnit == null) { 
                            employee.BusinessUnit = new Models.Catalog.BusinessUnit();
                            employee.BusinessUnit.Name = row[4].ToString(); 
                        }*/
                        employee.Position = _context.JobPosition.FirstOrDefault(po => po.Name == row[2].ToString());
                        if(employee.Position == null){ 
                            employee.Position = new Models.JobPosition();
                            employee.Position.Name =  row[2].ToString();
                        }
                        string dep = "Integer";
                        employee.Position.Department = _context.Department.FirstOrDefault(de => de.Name == dep);
                        if(employee.Position.Department == null){
                            employee.Position.Department = new Models.Catalog.Department();
                            employee.Position.Department.Name = dep;//row[3].ToString();
                        }
                        /*
                        employee.Shift = _context.Shifts.FirstOrDefault(sf => sf.Name == row[15].ToString());
                        if(employee.Shift == null){
                            employee.Shift = new Models.Catalog.Shift();
                            employee.Shift.Name = row[15].ToString();
                        }
                        employee.Direct = (row[8].ToString() == "D")? true : false;
                        employee.Hourly = (row[9].ToString() == "H")? true : false;
                        */
                        _context.Employee.Add(employee);
                        updated = updated + _context.SaveChanges();
                    }
                    //string text = dt.Rows[1][0].ToString();
                    
                    return Ok(updated);
                }
            }
            return BadRequest();
        }

        // DELETE: api/Employee/5
        [HttpDelete("{id}")]
        public async Task<ActionResult<Employee>> DeleteEmployee(Guid id)
        {
            var employee = await _context.Employee.FindAsync(id);
            if (employee == null)
            {
                return NotFound();
            }

            _context.Employee.Remove(employee);
            await _context.SaveChangesAsync();

            return employee;
        }

        private bool EmployeeExists(Guid id)
        {
            return _context.Employee.Any(e => e.Id == id);
        }
    }
}
