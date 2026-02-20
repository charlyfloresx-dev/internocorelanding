using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.ComponentModel.DataAnnotations;

namespace Interno.Production.Models
{
    public class Issue
    {
        [Key]
        public int Id { get; set; }
        [Required]
        public IssueType Type { get; set; }
        [Required]
        [MaxLength (250)]
        public string Description { get; set; }
        public bool Status { get; set; }
        public Issue(){
            this.Status = true;
        }
        public ProdIssueType ProdIssueType { get; set; }
    }

    public class ProdIssue : Issue
    {
        [Required]
        public ProdIssueType Level1 { get; set; }
        [Required]
        public string Level2 { get; set; }
        public string PIC { get; set; }
        public int Flag { get; set; }

        public ProdIssue(){
            this.Status = true;
        }
    }

    public enum IssueType
    {
        Personal = 0 ,
        Material = 1,
        Method = 2,
        Equipment = 3,
        Service = 4,
        Management = 5
    }

    public enum ProdIssueType
    {
        ScheduledStops = 0,
        EquipmentFailures = 1,
        PartsToolChange = 2,
        SettingAdjustement = 3,
        StartUp = 4,
        Others = 5,
        MinorStoppages =6,
        ReducedSpeed =7
    }
}