using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
namespace Interno.HealthCare.Models
{
    public class Specialty
    {
        [KeyAttribute]
        public int Id { get; set; }
        [Required]
        [MaxLength (150)]
        public string Name { get; set; }
        [Required]
        [MaxLength (150)]
        public string IdCertification { get; set; }
        [MaxLength (250)]
        public string Description { get; set; }
        [Required]
        [DataType(DataType.DateTime)]
        public DateTime CertificationDate { get; set;}
        [DataType(DataType.DateTime)]
        public DateTime ExpiredDate { get; set;}
        
        public virtual ICollection<Specialty> SubEspecialitys { get; set; } = new List<Specialty>();
    }
}