using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

using System.ComponentModel.DataAnnotations;

namespace Interno.Security.Models
{
    public class EmployeeLog : SecurityLog
    {
        [Required]
        public int EmployeeNumber { get; set; }
        public Interno.HumanResource.Models.Employee Employee { get; set; }
    }
}