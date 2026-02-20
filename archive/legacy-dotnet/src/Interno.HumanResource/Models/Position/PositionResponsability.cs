using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Interno.Domain.Catalog;

namespace Interno.HumanResource.Models
{
    public class PositionResposability
    {
        public int Id { get; set; }
        [Required]
        [MaxLength(250)]
        public string Description { get; set; }
        [Required]
        public double Percent { get; set; }
        [Required]
        [MaxLength(250)]
        public string Metric { get; set; }
        [Required]
        public Level Level { get; set; }
        [Required]
        public Required Required { get; set; }
        [NotMapped]
        public virtual ICollection<string> Skills { get; set; }  = new List<string>();
    }
}