using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Interno.HumanResource.Models;

namespace Interno.Action
{
    public class Action
    {
        [Key]
        public int Id { get; set; }
        public int AssignToNumber { get; set; }
        [NotMapped]
        public virtual Interno.HumanResource.Models.Employee AssignTo { get; set}
        [MaxLength(250)]
        public string Action { get; set; }
        public int MyProperty { get; set; }
        public DateTime CommitDate { get; set; }
        public DateTime ClosedDate { get; set; }
        public TimeSpan Transcurred { get { return (this.ClosedDate != DateTime.MinValue) ? this.ClosedDate - this.Created : TimeSpan.Zero; } }
        public DateTime Escalation { get; set; }

        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public DateTime Created { get; set; } = DateTime.Now;

        [TimestampAttribute]
        [DatabaseGenerated(DatabaseGeneratedOption.Computed)]
        public DateTime Updated { get; set; } = DateTime.Now;
    }
}