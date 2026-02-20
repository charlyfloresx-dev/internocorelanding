using System.ComponentModel.DataAnnotations;
namespace Interno.Domain.Catalog
{
    public class Level
    {
        [Key]
        public int Id { get; set; }
        [Required(ErrorMessage = "You should provide a level name value.")]
        [MaxLength(45)]
        public string Name { get; set; }
        [MaxLength(250)]
        public string Description { get; set; }
    }
}