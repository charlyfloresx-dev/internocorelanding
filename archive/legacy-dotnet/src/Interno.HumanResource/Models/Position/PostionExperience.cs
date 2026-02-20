using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Interno.Domain.Catalog;
using Interno.HumanResource.Models.Catalog;

namespace Interno.HumanResource.Models
{   
    public class PositionExperience
    {
        [KeyAttribute]
        public int Id { get; set; }
        [RequiredAttribute]
        public Miscellaneous InPosition { get; set; } //{ years: 5}
        [RequiredAttribute]
        public Miscellaneous InDepartment { get; set; } // months: 6
        [MaxLength(45)]
        public string Culture { get; set; }
        [NotMapped]
        public virtual ICollection<PositionExperienceIndustry> Industry { get; set; }
        [NotMapped]
        public virtual  ICollection<string> PreviousPosition { get; set; }
        [NotMapped]
        public virtual  ICollection<string> MomentumExperience { get; set;}
    }
}