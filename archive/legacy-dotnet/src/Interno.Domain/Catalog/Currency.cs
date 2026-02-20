using System.ComponentModel.DataAnnotations;
namespace Interno.Domain.Catalog
{
    public class Currency
    {
        [Key]
        [MaxLength(3)]
        public string Code { get; set; }
        [Required]
        [MaxLength(10)]
        public string Symbol { get; set; }
        [Required]
        [MaxLength(100)]
        public string Name { get; set; }
        public int DecimalDigits { get; set; }
        [MaxLength(105)]
        public string PluralName { get; set; }

    }
}