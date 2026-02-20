using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace Interno.HumanResource.Models.Catalog
{
    public class Break
    {
        [Key]
        public int Id { get; set; }
        [Required]
        [MaxLength(15)]
        public string Code { get; set;}
        [Required]
        public TimeSpan Start { get; set; }
        [Required]
        public TimeSpan End { get; set; }
        public BreakType Type { get; set; }
        [Required]
        public TimeSpan Duration { get; set; }
        [NotMapped]
        public virtual ICollection<BreaksGroup> BreakGroups { get; set; }
    }

    public class BreakType
    {
        [Key]
        public int Id { get; set;}
        [Required]
        [MaxLength(45)]
        public string Name { get; set; }
        [MaxLength(250)]
        public string Description { get; set; }
    }
    
    public class BreaksGroup{
        [Key]
        public int Id { get; set; }
        [Required]
        public int ShiftId { get; set; }
        public Shift Shift { get; set; }
        [Required]
        [MaxLength(45)]
        public string Name { get; set; }
        [MaxLength(250)]
        public string Description { get; set; }
        public virtual ICollection<Break> Breaks { get; set; }
    }
}