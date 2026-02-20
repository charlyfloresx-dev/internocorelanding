using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.ComponentModel.DataAnnotations;

namespace Interno.Production.Models
{
    public class ProductionArea : Interno.HumanResource.Models.Catalog.Area
    {
        [Required]
        public Facility Facility { get; set; }
        
    }
}