using System.ComponentModel.DataAnnotations;

using Interno.Domain.Catalog;

namespace Interno.HealthCare.Models
{
    public class Medicine
    {
        [Key]
        public int Id { get; set; }
        [Required]
        [MaxLength (45)]
        public string Code { get; set; }
        [Required]
        [MaxLength (150)]
        public string Name { get; set; }
        [Required]
        [MaxLength (250)]
        public string Formule { get; set; }
        [Required]
        [MaxLength (100)]
        public string Lote { get; set; }
        public decimal Qty { get; set; }
        public Interno.Domain.Catalog.UM Unit { get; set; }
        [MaxLength (100)]
        public string AdministrationWay { get; set; }
        [MaxLength (200)]
        public string Laboratory { get; set; }
        public decimal StdCost { get; set; }



    }
}