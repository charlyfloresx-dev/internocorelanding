using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.ComponentModel.DataAnnotations;

namespace Interno.Inventory.Models
{
    public class MaterialStatus
    {
        [Key]
        public int Id { get; set; }
        [Required]
        public string Code { get; set; }
        public string Description { get; set; }
        public HightestStatus Status { get; set; }
    }
    
    public enum HightestStatus
    {
        Preliminary,
        Definitive,
        Preview,
        Dissipate,
        Preparated,
        Partial,
        Started,
        Stopped,
        Flagged,
        Finished
    } 
}