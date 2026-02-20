using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;

namespace Interno.Domain.Models
{
    
    public partial class InternoClaim
    {
        [Key]
        public int Id { get; set; }
        
        [Required]
        public string User { get; set; }
     
        public string UserUserName { get; set; }
    
        [Required]
        public InternoRoles InternoRole { get; set; }
    
        [Required]
        public string Claim { get; set; }
    }

    
    public enum InternoRoles{
        Administrator = 1,
        Manager = 2,
        Supervisor = 3,
        Editor = 4,
        Creator = 5,
        Viewer = 6
    }
}