using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

using System.ComponentModel.DataAnnotations;

namespace Interno.Inventory.Models
{
    public class Partnership // Supplier / Customer
    {
        [Key]
        public int Id { get; set; }
        [Required]
        [MaxLength (15)]
        public string Code { get; set; }
        [Required]
        [MaxLength (250)]
        public string Name { get; set; }

        [Required]
        public PartnershipType Type { get; set; }
        public PartnershipStatus Status { get; set; }
    }
    public enum PartnershipType {
        Customer = 1, // Clientes
        Supplier = 2  // Proveedores
    }
    public enum PartnershipStatus {
        New,
        Standart,
        Silver,
        Gold,
        Platinum
    }
}