using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.ComponentModel.DataAnnotations;

namespace Interno.Inventory.Models
{
    public class ProductCategory
    {
        [Key]
        public int Id { get; set; }
        [Required]
        [MaxLength(45)]
        public string Name { get; set; }
        [Required]
        [MaxLength(250)]
        public string Description { get; set; }
    }
}