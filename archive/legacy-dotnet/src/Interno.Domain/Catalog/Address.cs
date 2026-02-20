using System.ComponentModel.DataAnnotations;
using Interno.Domain.Enum;

namespace Interno.Domain.Catalog
{
    public class Address
    {   
        [Key]
        public int Id { get; set; }
        [Required]
        public AddressType Type { get; set; }
        [Required]
        [StringLength(250)]
        public string AddressLine1 { get; set; }
        [StringLength(250)]
        public string AddressLine2 { get; set; }
        [Required]
        [StringLength(45)]
        public string City { get; set; }
        [Required]
        public int ZipCode { get; set; }
        [Required]
        [StringLength(100)]
        public string State { get; set; }
        [Required]
        [StringLength(100)]
        public string Country { get; set; }
        
        [StringLength(100)]
        public string Region { get; set; }
    }
}