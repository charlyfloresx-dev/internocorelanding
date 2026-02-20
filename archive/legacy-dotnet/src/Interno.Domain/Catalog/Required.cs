using System.ComponentModel.DataAnnotations;
namespace Interno.Domain.Catalog
{
    public class Required
    {
        [Key]
        public int id { get; set; }

        [Required(ErrorMessage = "You should provide a required name value.")]
        [MaxLength(45)]
        public string Name { get; set; }

        [MaxLength(250)]
        public string Description { get; set; }
    }
}