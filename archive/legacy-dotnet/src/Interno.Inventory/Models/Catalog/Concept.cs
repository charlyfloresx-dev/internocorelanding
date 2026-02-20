using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.ComponentModel.DataAnnotations;

namespace Interno.Inventory.Models
{
    public class Concept
    {
            [Key]
            public int Id { get; set; }            
            [Required]
            public string Name { get; set; }
            public string Description { get; set; }
            public ConceptType Type { get; set; }
            public bool AffectStock { get; set; }
        }
        public enum ConceptType
        {
            Entry = 1,
            Output = 2
        }  
}