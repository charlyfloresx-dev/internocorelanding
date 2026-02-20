using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace Interno.Domain.Catalog
{
    public class Location
    {
        [Key]
        public int Id { get; set; }
        [Required]
        [StringLength(45)]
        public string Name { get; set; }
        
        public Address Address { get; set; }
    }
}