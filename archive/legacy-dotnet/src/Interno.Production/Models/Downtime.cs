using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace Interno.Production.Models
{
    public class Downtime
    {
        [Key]
        public int Id { get; set; }
        public Guid Guid { get; set; }
        [Required]
        public int IssueId { get; set; }
        public Issue Issue { get; set; }
        [Required]
        public int ResultId { get; set; }
        public Result Result { get; set; } //Resource, Date, Linea, Estacion,WorkOrder
        [Required]
        public int RequestNumber { get; set; }
        [NotMapped]
        public virtual Interno.HumanResource.Models.Employee Request { get; set; }
        [MaxLength(250)]
        public string Description { get; set; }
        [Required]
        public Interno.Domain.Enum.StatusType Status { get; set; }
        public int AssignToNumber { get; set; }
        [NotMapped]
        public virtual Interno.HumanResource.Models.Employee AssignTo { get; set; }

        //Add Actions
        [MaxLength(250)]
        public string Action { get; set; }
        //[Required]
        public DateTime CommitDate { get; set; }
        public DateTime ClosedDate { get; set; }
        public TimeSpan Transcurred { get { return (this.ClosedDate != DateTime.MinValue) ? this.ClosedDate - this.Created : TimeSpan.Zero; } }
        public DateTime Escalation { get; set; }

        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public DateTime Created { get; set; } = DateTime.Now;
        [TimestampAttribute]
        [DatabaseGenerated(DatabaseGeneratedOption.Computed)]
        public DateTime Updated { get; set; } = DateTime.Now;

        public Downtime()
        {
            this.Guid = Guid.NewGuid();
        }
    }
}