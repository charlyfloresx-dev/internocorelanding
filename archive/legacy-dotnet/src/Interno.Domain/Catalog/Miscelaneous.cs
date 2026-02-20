using System.ComponentModel.DataAnnotations;

namespace Interno.Domain.Catalog
{
    public interface Miscellaneous
    {
        [Required]
        [MaxLength (45)]
        string Type { get; set; }
        [MaxLength (45)]
        string Value { get; set; }
    }
}