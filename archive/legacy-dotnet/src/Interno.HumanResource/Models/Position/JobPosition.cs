using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

using Interno.HumanResource.Models.Catalog;

namespace Interno.HumanResource.Models
{
    public class JobPosition
    {
        [Key]
        public int Id { get; set; }

        [Required]
        [MaxLength(250)]
        public string Name { get; set; }

        [Required]
        public Department Department { get; set; }
        //[Required]
        public Area Area { get; set; }
        //[Required]
        public Autority Autority { get; set; }
        //[Required]
        [DataType(DataType.Currency)]
        public double SalaryRangeFrom { get; set; }
        //[Required]
        [DataType(DataType.Currency)]
        public double SalaryRangeOut { get; set; }
        //[Required]
        public string Objetive { get; set; }

        public virtual ICollection<PositionResposability> Responsabilities { get; set; } = new List<PositionResposability>();
        [NotMapped]
        public PositionInOrganization Organization { get; set;}
        [NotMapped]
        public PositionExperience Experience { get; set; }
        [NotMapped]
        public virtual ICollection<PositionEducation> Education { get; set; } = new List<PositionEducation>();
        [NotMapped]
        public virtual ICollection<PositionLanguage> Language { get; set; } = new List<PositionLanguage>();
        [NotMapped]
        public virtual ICollection<PositionCompetences> Competences { get; set; }= new List<PositionCompetences>();

       // [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public DateTime Created { get; set; } = DateTime.UtcNow;
        //[TimestampAttribute]
        //[DatabaseGenerated(DatabaseGeneratedOption.Computed)]
        public DateTime Updated { get; set; } = DateTime.UtcNow;

        //public InternoUser InternoUser { get; set; }

        //public virtual ICollection<Approval> Approval { get; set; }
    }
}