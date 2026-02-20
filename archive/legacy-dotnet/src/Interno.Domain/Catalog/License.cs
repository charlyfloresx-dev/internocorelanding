using System.ComponentModel.DataAnnotations;

namespace Interno.Domain.Catalog
{
     public class License
    {
        [Key]
        public int Id { get; set; }
        [Required]
        [MaxLength (100)]
        public string LicenseName { get; set; }
        [Required]
        [MaxLength (25)]
        public string Type { get; set; }
        [MaxLength (100)]
        public string Number { get; set; }

    }
}