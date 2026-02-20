using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Interno.HumanResource.Models;
namespace Interno.Security.Models
{
    public class SecurityLog
    {
        [Key]
        public int Id { get; set; }
        [Required]
        public Guardhouse Guardhouse { get; set; }
        [Required]
        public DateTime Time { get; set; }
        [Required]
        public bool Type { get; set; } // Entrada/Salida
        [Required]
        public int SecurityGuardId { get; set; }
        public SecurityGuard SecurityGuard { get; set; }
    }
}