using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.ComponentModel.DataAnnotations;

namespace Interno.Production.Models
{
    public class Facility
    {
        [Key]
        public int Id { get; set; }
        [Required]
        [MaxLength (25)]
        public string Code { get; set; }
        [Required]
        [MaxLength (100)]
        public string Name { get; set; }

        public Interno.Domain.Catalog.Location Location { get; set; }

        public virtual ICollection<Interno.Inventory.Models.Warehouse> Warehouses { get; set; }
    }
}