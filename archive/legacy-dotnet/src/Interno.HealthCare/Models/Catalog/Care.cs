using System.ComponentModel.DataAnnotations;
namespace Interno.HealthCare.Models
{
    public class Care
    {
        [Key]
        public int Id { get; set; }
        [MaxLength (45)]
        public string Name { get; set; }
        [MaxLength (250)]
        public string Description { get; set; }
        public CareType Type { get; set; }
        public bool Managed { get; set; }
    }
}